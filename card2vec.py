"""A model for vectorizing Hearthstone cards."""
from typing import List, Optional

import torch
import torch.nn as nn


class Autoencoder(nn.Module):
    """A simple autoencoder model for compressing Hearthstone cards into a low-dimensional vector
    space, and then reconstructing the input (these are the encoder and decoder respectively).

    This architecture just consists of a set of linear layers for the encoder, and similary, a set
    of linear layers for the decoder. The output of the encoder describes the latent space of our
    data (the card embeddings).

    The encoder takes in as input a sequence of word embeddings describing the card text, the race
    of the card as a one-hot vector, the card class as a one-hot vector, the attack, the health,
    and the mana cost. The card text is preprocessed by feeding the sequence of tokens into a
    bidrectional LSTM and then concatenating the final hidden state for each token. The one-hot
    vectors are fed through an embedding layer. Finally, all the attributes are concatenated to
    form a single input vector.
    """
    # Private Instance Attributes:
    #   - _in_text_lstm: The LSTM layer used for preprocessing the card text.
    #   - _in_race_embedding: The embedding layer for the card race variable.
    #   - _in_classes_embedding: The embedding layer for the card class variable.
    #   - _enc_fc_layers: The layers defining the encoder.
    #   - _dec_fc_layers: The layers defining the decoder.
    _in_text_lstm: nn.LSTM
    _in_race_embedding: nn.Embedding
    _in_classes_embedding: nn.Embedding
    _enc_fc_layers: nn.Linear
    _dec_fc_layers: nn.Linear

    def __init__(self, max_text_length: int, word_embedding_size: int, num_races: int,
                 num_classes: int, lstm_size: int = 256, num_lstm_layers: int = 2,
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
        # LSTM that takes in the word embedding vector sequence
        self._in_text_lstm = nn.LSTM(
            word_embedding_size,
            lstm_size,
            num_layers=num_lstm_layers,
            dropout=0,
            bidirectional=True,
            batch_first=True  # Make the input and outputs have batch_size on the outer dim
        )
        # Layer that takes in the one-hot vector for the card race
        self._in_race_embedding = nn.Embedding((num_races + 1,), 10)
        # Layer that takes in the one-hot vector for the card class
        self._in_classes_embedding = nn.Embedding((num_classes + 1,), 10)

        num_stats = 3   # Attack, health, and cost
        input_dim = 2 * max_text_length * word_embedding_size + \
            self._in_race_embedding.embedding_dim + \
            self._in_classes_embedding.embedding_dim + num_stats

        # Initialize architecture to default if not given
        layer_sizes = layer_sizes or [128, 64, 12]
        # Encoder
        self._enc_fc_layers = []
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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Feed the given inputs through the encoder and decoder. Return the outputs of the decoder.

        Args:
            x: A tensor with shape (batch_size, preprocess_dim) in the format returned by the
               preprocess_inputs method, where preprocess_dim is the dim of the vectors returned
               by the preprocess_inputs method.

        Returns:
            A tensor with shape (batch_size, preprocess_dim)
        """"
        return self.decode(self.encode(x))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Return a tensor with shape (batch_size, layer_sizes[-1]) giving the encoded representation
        of the given inputs.

        Args:
            x: A tensor with shape (batch_size, preprocess_dim) in the format returned by the
               preprocess_inputs method, where preprocess_dim is the dim of the vectors returned
               by the preprocess_inputs method.
        """"
        # Feed through encoder
        for layer in self._enc_fc_layers:
            x = layer(x)
        return x

    def decode(self, x: torch.Tensor) -> torch.Tensor:
        """Return a tensor with shape (batch_size, preprocess_dim) giving the decoded representation
        of the given inputs in the format returned by the preprocess_inputs method, where
        preprocess_dim is the dim of the vectors returned by the preprocess_inputs method.

        Args:
            x: A tensor with shape (batch_size, layer_sizes[-1]) giving the encoded representation
               of the card in the latent-space.
        """"
        # Feed through decoder
        for layer in self._dec_fc_layers:
            x = layer(x)
        return x

    def preprocess_input(self, text: torch.Tensor, race: torch.Tensor, card_class: torch.Tensor,
                          attack: torch.Tensor, health: torch.Tensor, cost: torch.Tensor) \
            -> torch.Tensor:
        """Return a tensor with shape (batch_size, preprocess_dim) representing the given cards.

        Args:
            text: A tensor with shape (batch_size, max_text_length, word_embedding_size) containing
                  the embedding vectors for the tokens of the card text concatenated.
                  This sequence should be padded to max_text_length vectors (with zero vectors).
            race: A tensor with shape (batch_size, num_races + 1,) containing batch_size number of
                  (num_races + 1)-dimensional one-hot vectors where the last component indicates
                  that this card has no race (i.e. a NONE field).
            card_class: A tensor with shape (batch_size, card_class + 1,) containing batch_size
                        number of (card_class + 1)-dimensional one-hot vectors where the last
                        component indicates that this card has no class (i.e. a NONE field).
            attack: A tensor with shape (batch_size,) containing batch_size number of integers
                    indicating the the attack of each card.
            health: A tensor with shape (batch_size,) containing batch_size number of integers
                    indicating the the health of each card.
            cost: A tensor with shape (batch_size,) containing batch_size number of integers
                  indicating the the mana cost of each card.
        """
        # Process text
        text, _ = self._in_text_lstm(text)
        # LSTM returns a tensor with shape (batch_size, max_text_length, 2 * word_embedding_size)
        # Convert this to a 2D tensor by concatenating all time steps for further processing.
        # So, make it a tensor with shape (batch_size, 2 * max_text_length * word_embedding_size)
        batch_size = text.shape[0]
        text = text.contiguous().view(batch_size, -1)
        # Process other inputs
        race = self._in_race_embedding(race)  # Returns (batch_size, 10)
        card_class = self._in_classes_embedding(card_class)  # Returns (batch_size, 10)
        stats = torch.stack((attack, health, cost), dim=1)  # Returns (batch_size, 3)
        # Concatenate inputs (all tensors have shape (batch_size, X))
        # Returns (batch_size, sum x.shape[1] for all input tensors x)
        x = torch.cat((text, race, card_class, stats), dim=1)
        return x
