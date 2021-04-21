"""A model for vectorizing Hearthstone cards."""
import re
import json
import random
import numpy as np
from pathlib import Path
from collections import namedtuple
from typing import List, Generator, Optional, Union

import torch
import torch.nn as nn
import torch.optim as optim

import gensim.downloader
from num2words import num2words
from gensim.utils import simple_preprocess
from gensim.models import Word2Vec, KeyedVectors


class Autoencoder(nn.Module):
    """A simple autoencoder model for compressing Hearthstone cards into a low-dimensional vector
    space, and then reconstructing the input (these are the encoder and decoder respectively).

    This architecture just consists of a set of linear layers for the encoder, and similary, a set
    of linear layers for the decoder. The output of the encoder describes the latent space of our
    data (the card embeddings).

    The encoder takes in as input a sequence of word embeddings describing the card text, the race
    of the card as an index, the card class as an index, the attack, the health, and the mana cost.
    The card text is preprocessed by feeding the sequence of tokens into a bidrectional LSTM and
    then concatenating the final hidden state for each token. The categorical indices are fed
    through an embedding layer. Finally, all the attributes are concatenated to form a single input
    vector.
    """
    # Private Instance Attributes:
    #   - _in_text_lstm: The LSTM layer used for preprocessing the card text.
    #   - _in_race_embedding: The embedding layer for the card race variable.
    #   - _in_class_embedding: The embedding layer for the card class variable.
    #   - _enc_fc_layers: The layers defining the encoder.
    #   - _dec_fc_layers: The layers defining the decoder.
    _in_text_lstm: nn.LSTM
    _in_race_embedding: nn.Embedding
    _in_class_embedding: nn.Embedding
    _enc_fc_layers: nn.Linear
    _dec_fc_layers: nn.Linear

    def __init__(self, max_text_length: int, word_embedding_size: int, num_races: int,
                 num_classes: int, lstm_size: int = 64, num_lstm_layers: int = 2,
                 layer_sizes: Optional[List[int]] = None) -> None:
        """Initialise the Autoencoder.

        Args:
            max_text_length: The maximum length of the card text, in tokens.
            word_embedding_size: The dimensionality of the embedding vecetors used to represent the
                                tokens of the card text.
            num_races: The number of possible card races (categories).
            num_classes: The number of possible card classes (categories).
            lstm_size: The number of hidden units in the LSTM layer used to encode the card text.
            num_lstm_layers: The number of LSTM layers to stack.
            layer_sizes: A list containing the size of each layer in the encoder. The last element
                         in this list is the target dimensionality of the latent space. The decoder
                         is defined like the encoder, but with the layer sizes in reverse.

                         If not specified, then the autoencoder structure consists of 3 hidden
                         layers with 128, 64, and 12 units respectively.

        Preconditions:
            - len(layer_sizes) > 0
            - all(size > 0 for size in layer_sizes)
        """
        super().__init__()
        # LSTM that takes in the word embedding vector sequence
        self._in_text_lstm = nn.LSTM(
            word_embedding_size,
            lstm_size,
            num_layers=num_lstm_layers,
            dropout=0,
            bidirectional=True,
            batch_first=True  # Make the input and outputs have batch_size on the outer dim
        )
        # Layer that takes in the categorical index for the card race
        self._in_race_embedding = nn.Embedding(num_races, 4)
        # Layer that takes in the categorical index for the card class
        self._in_class_embedding = nn.Embedding(num_classes, 4)

        num_stats = 5   # Attack, health, cost, tier, is_golden
        input_dim = max_text_length * (2 * lstm_size) + \
            self._in_race_embedding.embedding_dim + \
            self._in_class_embedding.embedding_dim + num_stats

        # Initialize architecture to default if not given
        layer_sizes = layer_sizes or [128, 64, 12]
        # Encoder
        self._enc_fc_layers = nn.ModuleList()
        last_size = input_dim
        for size in layer_sizes:
            self._enc_fc_layers.append(nn.Linear(last_size, size))
            last_size = size
        # Decoder
        self._dec_fc_layers = []
        last_size = input_dim
        for size in layer_sizes:
            self._dec_fc_layers.append(nn.Linear(size, last_size))
            last_size = size
        # Reverse the order of the decoder layers
        self._dec_fc_layers.reverse()
        self._dec_fc_layers = nn.ModuleList(self._dec_fc_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Feed the given inputs through the encoder and decoder. Return the outputs of the
        decoder.

        Args:
            x: A tensor with shape (batch_size, preprocess_dim) in the format returned by the
               preprocess_inputs method, where preprocess_dim is the dim of the vectors returned
               by the preprocess_inputs method.

        Returns:
            A tensor with shape (batch_size, preprocess_dim)
        """
        return self.decode(self.encode(x))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Return a tensor with shape (batch_size, layer_sizes[-1]) giving the encoded
        representation of the given inputs.

        Args:
            x: A tensor with shape (batch_size, preprocess_dim) in the format returned by the
               preprocess_inputs method, where preprocess_dim is the dim of the vectors returned
               by the preprocess_inputs method.
        """
        # Feed through encoder
        for layer in self._enc_fc_layers:
            x = torch.relu(layer(x))
        return x

    def decode(self, x: torch.Tensor) -> torch.Tensor:
        """Return a tensor with shape (batch_size, preprocess_dim) giving the decoded
        representation of the given inputs in the format returned by the preprocess_inputs method,
        where preprocess_dim is the dim of the vectors returned by the preprocess_inputs method.

        Args:
            x: A tensor with shape (batch_size, layer_sizes[-1]) giving the encoded representation
               of the card in the latent-space.
        """
        # Feed through decoder
        for index, layer in enumerate(self._dec_fc_layers):
            x = layer(x)
            if index <= len(self._dec_fc_layers) - 1:
                x = torch.relu(x)
            else:
                x = torch.sigmoid(x)
        return x

    def preprocess_input(self, text: torch.Tensor, race: torch.Tensor, card_class: torch.Tensor,
                          attack: torch.Tensor, health: torch.Tensor, cost: torch.Tensor,
                          tier: torch.Tensor, is_golden: torch.Tensor) -> torch.Tensor:
        """Return a tensor with shape (batch_size, preprocess_dim) representing the given cards.

        Args:
            text: A tensor with shape (batch_size, max_text_length, word_embedding_size) containing
                  the embedding vectors for the tokens of the card text concatenated.
                  This sequence should be padded to max_text_length vectors (with zero vectors).
            race: A tensor with shape (batch_size,) containing batch_size number of indices.
            card_class: A tensor with shape (batch_size,) containing batch_size number of indices
            attack: A tensor with shape (batch_size,) containing batch_size number of integers
                    indicating the the attack of each card.
            health: A tensor with shape (batch_size,) containing batch_size number of integers
                    indicating the the health of each card.
            cost: A tensor with shape (batch_size,) containing batch_size number of integers
                  indicating the the mana cost of each card.
            tier: A tensor with shape (batch_size,) containing batch_size number of integers
                  indicating the tier of each card.
            is_golden: A tensor with shape (batch_size,) containing batch_size number of binary
                       values indicating whether each card is regular or golden
                       (0 and 1 respectively).
        """
        # Process text
        text, _ = self._in_text_lstm(text)
        # LSTM returns a tensor with shape (batch_size, max_text_length, 2 * lstm_size)
        # Convert this to a 2D tensor by concatenating all time steps for further processing.
        # So, make it a tensor with shape (batch_size, 2 * max_text_length * lstm_size)
        batch_size = text.shape[0]
        text = text.contiguous().view(batch_size, -1)
        # Process other inputs
        race = self._in_race_embedding(race)  # Returns (batch_size, race_dim)
        card_class = self._in_class_embedding(card_class)  # Returns (batch_size, class_dim)
        # stats is a tensor with shape (batch_size, 5)
        stats = torch.stack((attack, health, cost, tier, is_golden), dim=1)
        # Concatenate inputs (all tensors have shape (batch_size, X))
        # Returns (batch_size, sum x.shape[1] for all input tensors x)
        x = torch.cat((text, race, card_class, stats), dim=1)
        return x

    def train(self, training_data: List[tuple], epochs: int = 10, batch_size: int = 128,
              log_frequency: int = 10, no_cuda: bool = False) -> None:
        """Train this model with the given data."""
        device = torch.device('cuda:0' if torch.cuda.is_available() and not no_cuda else 'cpu')
        self.to(device)
        print(f'Training on {device}')

        loss_function = nn.MSELoss()
        optimizer = optim.Adam(self.parameters())

        for epoch in range(epochs):
            running_loss = 0
            for index, data in enumerate(batch_training_data(training_data, batch_size)):
                # Preprocess card data
                inputs = self.preprocess_input(
                    torch.stack([x[0].to(device) for x in data]),
                    torch.as_tensor([x[1] for x in data], device=device),
                    torch.as_tensor([x[2] for x in data], device=device),
                    torch.as_tensor([x[3] for x in data], device=device),
                    torch.as_tensor([x[4] for x in data], device=device),
                    torch.as_tensor([x[5] for x in data], device=device),
                    torch.as_tensor([x[6] for x in data], device=device),
                    torch.as_tensor([x[7] for x in data], device=device),
                )
                inputs = inputs.to(device)
                # Zero the parameter gradients
                optimizer.zero_grad()
                outputs = self.forward(inputs)
                loss = loss_function(outputs, inputs)
                loss.backward()
                optimizer.step()

                # Statistics
                running_loss += loss.item()
                if (index + 1) % log_frequency == 0:
                    print('[%d, %5d] loss: %.3f' % (epoch + 1, index + 1,
                        running_loss / log_frequency))
                    running_loss = 0


def batch_training_data(data: List[tuple], batch_size) -> Generator:
    """Batch the given training data. Continously yield lists where, except for possibly the last
    one, each list has batch_size elements contiguously chosen from the original list.
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def load_training_data(card_data_filepath: Path,
                       word2vec_model: Union[str, Path] = 'glove-wiki-gigaword-50',
                       augment_word_embeddings: bool = True, shuffle: bool = True) -> tuple:
    """Load the training data from a json file containing Hearthstone cards.

    Args:
        card_data_filepath: Filepath to a json file containing a list of card objects in the
                            format given by the HearthstoneJSON data api. Embedding vectors are
                            built from the textual descriptions and card attributes given in
                            this file.
        word2vec_model: Filepath to a word2vec model checkpoint or the name of a pre-trained
                        model corresponding to the gensim-data models available from
                        https://github.com/RaRe-Technologies/gensim-data/.
                        If not specified, then defaults to the ``glove-wiki-gigaword-50`` model.
        augment_word_embeddings: Whether to augment the word embeddings with words from the
                                 Hearthstone game vocabulary.
        shuffle: Whether to shuffle the data.

    Returns:
        A tuple of the form (data, max_text_length, word_embedding_size, num_races, num_classes).

        data is a list of tuples of the form (encoded_text, encoded_race, encoded_class, attack,
        health, cost, tier, is_golden), where encoded_text is a tensor with shape (max_text_length,
        word_embedding_size), and encoded_race and encoded_class are tensors with shape
        (num_races,) and (num_classes,) respectively.
    """
    word_embeddings = load_word2vec_embeddings(word2vec_model)
    if augment_word_embeddings:
        init_special_hs_embeddings(word_embeddings)

    with open(card_data_filepath, encoding='utf-8') as fp:
        card_data = json.load(fp)

    cards = []
    all_races = set()
    all_classes = set()
    # A set containing the names of processed cards
    visited = set()

    for data in card_data:
        card = load_card_from_dict(data, default_race='none', default_card_class='none')
        if card.name is not None:
            key = card.name
            if card.is_golden:
                key += '_golden'

            # Ignore this card if we've already processed it
            if key in visited:
                continue
            visited.add(key)

        all_races.add(card.race)
        all_classes.add(card.card_class)
        cards.append(card)

    # Sort the categorical data so that the indices are consistent across runs.
    all_races = sorted(all_races)
    all_classes = sorted(all_classes)

    # Tokenize each card and find the maximum length
    tokens_by_card = {
        card: simple_preprocess(card.text, min_len=0, max_len=float('inf'))
        for card in cards
    }
    max_text_length = max(len(x) for x in tokens_by_card.values())

    data = []
    for card in cards:
        # Encode text
        encoded_text = torch.zeros((max_text_length, word_embeddings.vector_size))
        for index, token in enumerate(tokens_by_card[card]):
            if token in word_embeddings:
                # Copy the embedding vector since word_embeddings returns non-writeable numpy
                # arrays. However, PyTorch does not support non-writeable arrays.
                vector = torch.as_tensor(np.copy(word_embeddings.get_vector(token)))
            else:
                vector = torch.zeros((word_embeddings.vector_size,))
            encoded_text[index] = vector
        # Encode race
        encoded_race = all_races.index(card.race)
        # Encode card class
        encoded_class = all_classes.index(card.card_class)
        data.append((encoded_text, encoded_race, encoded_class, card.attack, card.health, card.cost,
                     card.tier, int(card.is_golden)))

    if shuffle:
        random.shuffle(data)
    return (data, max_text_length, word_embeddings.vector_size, len(all_races), len(all_classes))


Card = namedtuple('Card', 'name text race card_class attack health cost tier is_golden')


def load_card_from_dict(data: dict, default_race: Optional[str] = None,
                        default_card_class: Optional[str] = None) -> Card:
    """Return the card given by data."""
    name = data.get('name', None)
    text = clean_card_text(data.get('text', ''))
    race = data.get('race', default_race)
    card_class = data.get('cardClass', default_card_class)
    attack = data.get('attack', 0)
    health = data.get('health', 0)
    cost = data.get('cost', 0)
    tier = data.get('tier', 0)
    is_golden = data.get('is_golden', False)

    return Card(name, text, race, card_class, attack, health, cost, tier, is_golden)


def clean_card_text(text: str) -> str:
    """Clean a card description."""
    text = text.replace('[x]', '')
    # Remove html tags
    text = re.sub(r'<.*?>', '', text)
    # Replace "+X/+Y" with "X attack and Y health"
    replace_func = lambda x: '{} attack and {} health'.format(x.group(1), x.group(2))
    text = re.sub(r'\+(\d*)\/\+(\d*)', replace_func, text)
    # Replace numbers with word representation
    text = re.sub(r'(\d+)', lambda x: num2words(int(x.group(0))), text)
    return text


def load_word2vec_embeddings(model: Union[str, Path]) -> KeyedVectors:
    """Return the word embeddings learned from the given word2vec model."""
    # Load card data and construct embeddings
    model_keys = list(gensim.downloader.info()['models'].keys())
    # Load model vectors as a KeyedVectors object
    if isinstance(model, str) and model in model_keys:
        # model is the name of a pre-trained model
        return gensim.downloader.load(model)
    else:
        # model is a path to a model checkpoint
        return Word2Vec.load(str(model)).wv
    raise ValueError(f'failed to load word2vec model "{model}"')


def init_special_hs_embeddings(word_embeddings: KeyedVectors) -> None:
    """Initialise embeddings for special Hearthstone words such as "Deathrattle" and "Murloc".
    """
    if 'deathrattle' not in word_embeddings:
        # Use the average of the vectors for "death" and "rattle" as a proxy
        v = (word_embeddings.get_vector('death') + word_embeddings.get_vector('rattle')) / 2
        word_embeddings.add_vector('deathrattle', v)

    if 'deathrattles' not in word_embeddings:
        # Use the vector for "battlecry" as a proxy
        v = word_embeddings.get_vector('deathrattle')
        word_embeddings.add_vector('deathrattles', v)

    if 'battlecry' not in word_embeddings:
        # Use the average of the vectors for "battle" and "cry" as a proxy
        v = (word_embeddings.get_vector('battle') + word_embeddings.get_vector('cry')) / 2
        word_embeddings.add_vector('battlecry', v)

    if 'battlecries' not in word_embeddings:
        # Use the vector for "battlecry" as a proxy
        v = word_embeddings.get_vector('battlecry')
        word_embeddings.add_vector('battlecries', v)

    if 'windfury' not in word_embeddings:
        # Use the average of the vectors for "wind" and "fury" as a proxy
        v = (word_embeddings.get_vector('wind') + word_embeddings.get_vector('fury')) / 2
        word_embeddings.add_vector('windfury', v)

    if 'windfuries' not in word_embeddings:
        # Use the vector for "windfury" as a proxy
        v = word_embeddings.get_vector('windfury')
        word_embeddings.add_vector('windfuries', v)

    if 'murloc' not in word_embeddings:
        # Use the vector for "fish" as a proxy
        v = word_embeddings.get_vector('fish')
        word_embeddings.add_vector('murloc', v)

    if 'murlocs' not in word_embeddings:
        # Use the vector for "fishes" as a proxy
        v = word_embeddings.get_vector('fishes')
        word_embeddings.add_vector('murlocs', v)
