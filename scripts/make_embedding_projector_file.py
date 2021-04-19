"""Make a TSV file representing the given word2vec model checkpoint in the format
of the tensorflow embedding projector.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import argparse
from pathlib import Path
from gensim.models import Word2Vec


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    model = Word2Vec.load(str(args.model_checkpoint))

    if args.words_filepath is not None:
        with open(args.words_filepath) as fp:
            words = set(fp.read().splitlines())
    else:
        words = None

    if args.output_filepath is None:
        args.output_filepath = args.model_checkpoint.with_suffix('.tsv')

    extension = args.output_filepath.suffix
    metadata_filename = args.output_filepath.with_suffix('').name + '_metadata' + extension
    metadata_filepath = args.output_filepath.parent / metadata_filename
    with open(args.output_filepath, 'w+') as output_fp,\
         open(metadata_filepath, 'w+') as metadata_fp:
        # Write data
        for word in model.wv.index_to_key:
            if words is not None and word not in words:
                continue
            line = '\t'.join(str(x) for x in model.wv[word])
            output_fp.write(line + '\n')
            metadata_fp.write(word + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make the embedding projector TSV file.')
    parser.add_argument('model_checkpoint', type=Path, help='The path to the model checkpoint.')
    parser.add_argument('output_filepath', default=None, type=Path,
                        help='The name of the output file.')
    parser.add_argument('--words', dest='words_filepath', required=False, type=Path,
                        help='The path to a file containing a list of words, '
                             'separated by a new line. '
                             'If specified, only words from this list are included in the output.')
    main(parser.parse_args())
