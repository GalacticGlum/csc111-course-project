"""Scrape pages from the Hearthstone wiki."""
import json
import requests
import argparse
from pathlib import Path
from typing import Tuple, List, Optional
from urllib.parse import quote as url_quote

from tqdm import tqdm


API_URL = 'https://hearthstone.fandom.com/api.php?action={action}&format=json'


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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape pages from the Hearthstone wiki.')
    parser.add_argument('output_directory', type=Path, help='Directory to save pages.')
    args = parser.parse_args()
    scrape_pages(args.output_directory)