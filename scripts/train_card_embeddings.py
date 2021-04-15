"""Train or fine-tune a card embedding model on a corpus."""
import argparse
import time
from pathlib import Path
from typing import Iterator, List, Optional

import tensorflow as tf
from gensim.models import  Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
from gensim.utils import simple_preprocess, RULE_KEEP


class SentenceIterator:
    """An iterator that yields sentences (lists of str)."""
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath

    def __iter__(self) -> Iterator[List[str]]:
        for line in open(self.filepath, encoding='utf-8'):
            words = simple_preprocess(line, min_len=0, max_len=float('inf'))
            yield words


class MonitorCallback(CallbackAny2Vec):
    """A callback for monitoring the progress of the card2vec model."""
    # Private Instance Attributes:
    #   - _epoch: The current epoch.
    #   - _loss_previous_steps: The loss at the previous step.
    #   - _summary_writer: The TensorBoard summar writer.
    #   - _log_frequency: The frequency at which to log stats, in epochs.
    #   - _save_frequency: The frequency at which to save the model.
    #   - _output_path: The directory to save model checkpoints.
    _epoch: int
    _loss_previous_step: float
    _summary_writer: Optional[tf.summary.SummaryWriter]
    _log_frequency: int
    _save_frequency: int
    _output_path: Optional[Path]

    def __init__(self, output_path: Optional[Path] = None,
                 log_frequency: int = 1,
                 save_frequency: int = 100,
                 summary_writer: Optional[tf.summary.SummaryWriter] = None) \
            -> None:
        self._epoch = 0
        self._loss_previous_step = 0
        self._summary_writer = summary_writer
        self._log_frequency = log_frequency
        self._save_frequency = save_frequency
        self._output_path = output_path

    def on_epoch_end(self, model: Word2Vec) -> None:
        """Called when an epoch ends."""
        loss = model.get_latest_training_loss()
        delta_loss = loss - self._loss_previous_step
        print(f'Epoch {self._epoch} - Loss: {delta_loss}')

        log = self._epoch % self._log_frequency == 0
        if self._summary_writer is not None and log:
            with self._summary_writer.as_default():
                tf.summary.scalar('loss', delta_loss, step=self._epoch)

        save = self._epoch > 0 and self._epoch % self._save_frequency == 0
        if self._output_path is not None and save:
            model.save(str(self._output_path / f'checkpoint-{self._epoch}.model'))

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

    if args.line_by_line:
        dataset = SentenceIterator(args.corpus_filepath)
    else:
        corpus_text = args.corpus_filepath.read_text(encoding='utf-8')
        dataset = simple_preprocess(corpus_text, min_len=0, max_len=float('inf'))

    print('Started training model...')
    start_time = time.time()
    model = Word2Vec(
        sentences=dataset,
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
        callbacks=[MonitorCallback(output_path, args.log_freq, args.save_freq, summary_writer)],
        trim_rule=lambda x, y, z: RULE_KEEP,  # Keep all words, and don't perform trimming!
        max_vocab_size=None,
        max_final_vocab=None
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
    parser.add_argument('--no-line-by-line', dest='line_by_line', action='store_false',
                        help='Whether to load the corpus line by line, or all at once. '
                             'Note that loading it all at once (potentially) requires a lot of RAM.')
    parser.add_argument('--run-name', type=str, default=None,
                        help='The name of the run. If unspecified, defaults to the name of the '
                        'first file in the given corpus.')
    parser.add_argument('-b', '--batch-size', type=int, default=256,
                        help='The size of a single training batch. Defaults to 256.')
    parser.add_argument('-e', '--epochs', type=int, default=300,
                        help='The number of times to iterate over the dataset '
                              'while training. Defaults to 1.')
    parser.add_argument('--initial-lr', type=float, default=0.025,
                        help='The initial learning rate.')
    parser.add_argument('--target-lr', type=float, default=1e-4,
                        help='The target learning rate.')
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help='Sets the seed of the random engine. '
                              'If unspecified, a random seed is chosen.')
    parser.add_argument('--log-freq', type=int, default=1,
                        help='The frequency at which to log stats, in epochs. Defaults to 1.')
    parser.add_argument('--save-freq', type=int, default=100,
                        help='The frequency at which to save the model, '
                             'in epochs. Defaults to 100.')
    parser.add_argument('--num-workers', type=int, default=8,
                        help='The number of workers to use. Defaults to 8.')
    main(parser.parse_args())