"""Train a card embedding model on a corpus."""
import argparse
import time
from pathlib import Path
from typing import Iterator, List, Optional

import tensorflow as tf
from gensim.models import  Word2Vec
from gensim.utils import simple_preprocess
from gensim.models.callbacks import CallbackAny2Vec
from gensim.test.utils import common_texts


class Corpus:
    """An iterator that yields sentences (lists of str)."""
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath

    def __iter__(self) -> Iterator[List[str]]:
        for line in open(self.filepath):
            yield simple_preprocess(line)


class MonitorCallback(CallbackAny2Vec):
    """A callback for monitoring the progress of the card2vec model."""
    def __init__(self, summary_writer: Optional[tf.summary.SummaryWriter] = None):
        self._epoch = 0
        self._loss_previous_step = 0
        self._summary_writer = summary_writer

    def on_epoch_end(self, model: Word2Vec):
        loss = model.get_latest_training_loss()
        delta_loss = loss - self._loss_previous_step
        print(f'Epoch {self._epoch} - Loss: {delta_loss}')

        if self._summary_writer is not None:
            with self._summary_writer.as_default():
                tf.summary.scalar('loss', delta_loss, step=self._epoch)

        self._epoch += 1
        self._loss_previous_step = loss


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    # Get run name
    run_name = args.run_name or args.corpus_filepath.stem
    output_path = args.output_dir / f'{run_name}'
    # Make output directory, if it does not already exist
    output_path.mkdir(exist_ok=True, parents=True)
    summary_writer = tf.summary.create_file_writer(str(output_path))

    print('Started training model...')
    start_time = time.time()
    model = Word2Vec(
        sentences=Corpus(args.corpus_filepath),
        vector_size=args.hidden_size,
        workers=args.num_workers,
        min_count=0,  # Don't ignore any words by frequency
        window=args.window_size,
        sg=True,  # Use skip-gram algorithm
        negative=args.n_negative_samples,
        ns_exponent=args.ns_lambda_power,
        alpha=args.initial_lr,
        min_alpha=args.target_lr,
        seed=args.seed,
        epochs=args.epochs,
        batch_words=args.batch_size,
        compute_loss=True,
        callbacks=[MonitorCallback(summary_writer)]
    )

    elapsed_time = time.time() - start_time
    print(f'Finished training model (took {elapsed_time:2f} seconds)')

    # Save the model
    model.save(str(output_path / 'final.model'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train a card embedding model on a corpus.')
    parser.add_argument('corpus_filepath', type=Path,
                        help='Name of text files to train on (the corpus).')
    parser.add_argument('-o', '--output-dir', type=Path, default='./output/card2vec/',
                        help='Output directory to save model weights, embeddings, and vocab.')
    # Model configuration
    parser.add_argument('-w', '--window-size', type=int, default=10,
                        help='The size of the sliding window (context window). Defaults to 10.')
    parser.add_argument('-ns', '--n-negative-samples', type=int, default=5,
                        help='Number of negative samples to construct per positive sample. '
                        'Defaults to 5, meaning that 6N training examples are created, '
                        'where N is the number of positive samples.')
    parser.add_argument('-hs', '--hidden-size', type=int, default=10,
                        help='The number of units in the hidden layers. '
                        'The dimensionality of the embedding vectors. Defaults to 10.')
    parser.add_argument('--lambda', dest='ns_lambda_power', type=float, default=0.75,
                        help='Used to skew the probability distribution when sampling words.')
    # Training configuration
    parser.add_argument('--run-name', type=str, default=None,
                        help='The name of the run. If unspecified, defaults to the name of the '
                        'first file in the given corpus.')
    parser.add_argument('-b', '--batch-size', type=int, default=256,
                        help='The size of a single training batch. Defaults to 256.')
    parser.add_argument('-e', '--epochs', type=int, default=300,
                        help='The number of times to iterate over the dataset '
                              'while training. Defaults to 1.')
    parser.add_argument('--initial-lr', type=float, default=0.1,
                        help='The initial learning rate.')
    parser.add_argument('--target-lr', type=float, default=1e-4,
                        help='The target learning rate.')
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help='Sets the seed of the random engine. '
                              'If unspecified, a random seed is chosen.')
    parser.add_argument('--num-workers', type=int, default=8,
                        help='The number of workers to use. Defaults to 8.')
    main(parser.parse_args())