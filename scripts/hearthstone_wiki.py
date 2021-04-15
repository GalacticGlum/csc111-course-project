"""Tools for scraping, cleaning, and processing pages from the Hearthstone wiki."""
import re
import json
import requests
import argparse
from pathlib import Path
from typing import Tuple, List, Optional
from urllib.parse import quote as url_quote

import click
import pypandoc
import contractions
from tqdm import tqdm
from num2words import num2words

from hsbg.utils import parallel_map


# Base api url for the Hearthstone wiki
API_URL = 'https://hearthstone.fandom.com/api.php?action={action}&format=json'
# A regex pattern to find hypenated words.
HYPENATED_WORDS_PATTERN = re.compile(r'(\w+)(-)(\w+)')
# A Regex pattern to match urls starting with or without http(s).
URL_MATCH_PATTERN = re.compile(
    r'(?i)(https?:\/\/(?:www\.|(?!www))'
    r'[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9]+\.[^\s]{2,})'
)


def request_from_api(params: dict) -> dict:
    """Perform an api request and return the json response."""
    url = API_URL.format(**params)
    request = requests.get(url, params=params)
    try:
        return request.json()
    except ValueError:
        raise ValueError('Your request to the url "{url}" with the paramaters'
                         '"{params}" returned data in a format other than JSON.'
                         'Please check your input data.'.format(url=url, params=params))


def get_pages(from_page: Optional[str] = '') -> Tuple[List[dict], Optional[str]]:
    """Return a list of dicts containing two keys: the id of the page (``id``), and
    the title of the page (``title``), and the page to continue from, if any.

    Args:
        from_page: The title of the page to start enumerating from.
    """
    params = {
        'action': 'query',
        'list': 'allpages',
        'aplimit': 'max',
        'apfrom': from_page or '',
    }

    request = request_from_api(params)
    pages = [{
        'id': page['pageid'],
        'title': page['title']
    } for page in request['query']['allpages']]

    try:
        next_page = request['continue']['apcontinue']
    except:
        next_page = None

    return pages, next_page


def get_page_wikitext(page_id: int) -> str:
    """Return the wikitext for the page with the given id."""
    params = {
        'action': 'parse',
        'pageid': page_id,
        'formatversion': 2,
        'prop': 'wikitext'
    }

    request = request_from_api(params)
    try:
        return request['parse']['wikitext']
    except:
        raise ValueError(f'Failed to retrieve wikitext for page with id "{page_id}".')


def scrape_pages(output_directory: Path) -> None:
    """Scrape pages from the Hearthstone wiki and save them in the given directory."""
    output_directory.mkdir(parents=True, exist_ok=True)

    from_page = ''
    while from_page is not None:
        pages, from_page = get_pages(from_page)
        for page in tqdm(pages):
            page_id = page['id']
            wikitext = get_page_wikitext(page_id)
            filepath = output_directory / f'{page_id}_wikitext.txt'
            with open(filepath, 'w+', encoding='utf-8') as fp:
                fp.write(wikitext)


def clean_pages(directory: Path, glob_pattern: Optional[str] = None, num_workers: int = 4) \
        -> None:
    """Clean the wikitext data. The given directory should only contain text
    files with wikitext data.

    NOTE: This is an IRREVERSIBLE operation, and will remove files!
    """
    pattern = '**/*.txt' or glob_pattern
    files = list(directory.glob(pattern))
    total_files = len(files)

    def _clean_file(filepath: Path) -> None:
        """Clean the given file."""
        text = filepath.read_text(encoding='utf-8')
        # If the page starts with a REDIRECT or only has a few words, then just ignore it!
        if text.startswith('#REDIRECT') or len(text.split()) <= 10:
            filepath.unlink()

    parallel_map(files, _clean_file, n_jobs=num_workers)
    remaining_files = len(list(directory.glob(pattern)))
    print('Removed {} files'.format(total_files - remaining_files))


def convert_pages(directory: Path, output_directory: Optional[Path] = None,
                  glob_pattern: Optional[str] = None, num_workers: int = 4) \
        -> None:
    """Convert wikitext data into raw text with pandoc. The given directory should only
    contain text files with wikitext data.
    """
    # Get files
    pattern = '**/*.txt' or glob_pattern
    files = list(directory.glob(pattern))

    output_directory = output_directory or directory
    output_directory.mkdir(parents=True, exist_ok=True)

    def _convert_file(filepath: Path) -> None:
        """Convert the given file."""
        output_filepath = output_directory / (filepath.stem + '_converted.txt')
        # Convert from wikitext to txt
        pypandoc.convert_file(
            str(filepath),
            'plain',
            format='mediawiki',
            outputfile=str(output_filepath)
        )

    parallel_map(files, _convert_file, n_jobs=num_workers)


def make_corpus_from_pages(directory: Path, output_filepath: Path,
                           glob_pattern: Optional[str] = None) -> None:
    """Make a Hearthstone wiki corpus from converted wikitext files."""
    pattern = '**/*.txt' or glob_pattern
    files = list(directory.glob(pattern))
    with open(output_filepath, 'w+', encoding='utf-8') as fp:
        for file in tqdm(files):
            text = file.read_text(encoding='utf-8')
            # Remove links
            text = re.sub(URL_MATCH_PATTERN, '', text)
            # Expand contractions
            text = contractions.fix(text)
            # Replace hyphenated words
            text = re.sub(HYPENATED_WORDS_PATTERN, r'\1_\3', text)
            # Replace "+X/+Y" with "X attack and Y health"
            replace_func = lambda x: ' {} attack and {} health '.format(
                num2words(int(x.group(1))),
                num2words(int(x.group(2)))
            )
            text = re.sub(r'\+?(\d+)\/\+?(\d+)', replace_func, text)
            # Replace special characters
            text = text.replace('|', ' ')
            text = text.replace('"', '')
            text = text.replace('“', '')
            text = text.replace('”', '')
            # Output text to corpus file
            fp.write(text + '\n')


if __name__ == '__main__':
    @click.group()
    def cli() -> None:
        """Tools for scraping, cleaning, and processing pages from the Hearthstone wiki."""

    @cli.command()
    @click.argument('output_directory', type=Path)
    def scrape(output_directory: Path) -> None:
        """Scrape pages from the Hearthstone wiki."""
        scrape_pages(output_directory)

    @cli.command()
    @click.argument('directory', type=Path)
    @click.option('--glob_pattern', '-g', type=str, default=None)
    @click.option('--num_workers', '-w', type=int, default=8)
    def clean(directory: Path, glob_pattern: Optional[str], num_workers: int) -> None:
        """Clean the wikitext data. The given directory should only contain text
        files with wikitext data.

        NOTE: This is an IRREVERSIBLE operation, and will remove files!
        """
        message = 'This is an IRREVERSIBLE operation, and will remove files! '\
                  'Do you want to continue'
        if click.confirm(message, default=True):
            clean_pages(directory, glob_pattern=glob_pattern, num_workers=num_workers)

    @cli.command()
    @click.argument('directory', type=Path)
    @click.option('--output-directory', '-o', type=Path, default=None)
    @click.option('--glob_pattern', '-g', type=str, default=None)
    @click.option('--num_workers', '-w', type=int, default=8)
    def convert(directory: Path, output_directory: Optional[Path],
                glob_pattern: Optional[str], num_workers: int) -> None:
        """Convert wikitext data into raw text with pandoc. The given directory should only
        contain text files with wikitext data.
        """
        convert_pages(directory, output_directory, glob_pattern=glob_pattern, num_workers=num_workers)

    @cli.command()
    @click.argument('directory', type=Path)
    @click.argument('output_filepath', type=Path)
    @click.option('--glob_pattern', '-g', type=str, default=None)
    def make_corpus(directory: Path, output_filepath: Path, glob_pattern: Optional[str]) -> None:
        """Make a Hearthstone wiki corpus from converted wikitext files."""
        make_corpus_from_pages(directory, output_filepath, glob_pattern=glob_pattern)

    # Start cli
    cli()
