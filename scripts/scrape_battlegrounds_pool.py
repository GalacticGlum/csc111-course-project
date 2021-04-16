"""Scrape the Hearthstone Battlegrounds card pool from
https://www.hearthpwn.com/cards?display=1&filter-set=1117.

This script outputs a json file containing a list of minions with their tavern tier.
"""

import json
import argparse
from enum import Enum
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup


ROOT_URI = 'https://hearthstone.fandom.com'
DATA_URL = f'{ROOT_URI}/wiki/Category:Battlegrounds_card_data'


@dataclass
class Card:
    """A Hearthstone card.

    Instance Attributes:
        - name: The name of the card.
        - tier: The tavern tier of the card (or None if not tier).
        - is_golden: Whether it is a golden card.
        - is_removed: Whether the card has been removed from the current version of Hearthstone.
    """
    name: str
    tier: Optional[int]
    is_golden: bool
    is_removed: bool

    def to_dict(self) -> dict:
        """Return a json-serializable dict representation of this card."""
        return {
            'name': self.name,
            'tier': self.tier,
            'is_golden': self.is_golden,
            'is_removed': self.is_removed
        }


def get_card(url: str) -> Card:
    """Return the card at the given url.

    Args:
        url: The url of the card's wiki page.
    """
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    tier_icon_element = soup.find('span', class_='resource-icon tier-icon')
    if tier_icon_element is not None:
        tier = int(tier_icon_element.parent.text.replace('\n', '').strip())
    else:
        tier = None

    is_removed = soup.find('img', alt='Icon delete.png') is not None
    name = soup.find('div', class_='title').text

    infobox_title = soup.find('div', class_='card-infobox-image-title')
    if infobox_title is not None:
        is_golden = infobox_title.text == 'BG Gold'
    else:
        is_golden = False

    return Card(name, tier, is_golden, is_removed)


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    if args.output.exists() and not args.overwrite:
        raise ValueError(f'The given output file \'{args.output.absolute()}\' already exists! '
                         'Use the --overwrite flag to ignore this.')
    cards_by_tier = {}
    # Get wiki html and parse it
    soup = BeautifulSoup(requests.get(DATA_URL).content, 'html.parser')
    while soup is not None:
        for link in tqdm(soup.select('div[class=\'mw-category-group\'] li a')):
            card_url = ROOT_URI + link['href']
            card = get_card(card_url)

            if card.is_removed and args.ignore_removed:
                continue
            tier = card.tier or 'NA'
            if tier not in cards_by_tier:
                cards_by_tier[tier] = []
            cards_by_tier[tier].append(card.to_dict())

        pagination_elements = soup.find_all('a', string='next page')
        if len(pagination_elements) == 0:
            # There are no more pages left, so we are done!
            soup = None
        else:
            next_page_url = ROOT_URI + pagination_elements[0]['href']
            soup = BeautifulSoup(requests.get(next_page_url).content, 'html.parser')

    with open(args.output, 'w+') as fp:
        json.dump(cards_by_tier, fp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape the Hearthstone Battlegrounds card pool.')
    parser.add_argument('-o', '--output', type=Path, default=None,
                        help='The filepath of the output json file.')
    parser.add_argument('--overwrite', action='store_true', dest='overwrite',
                        help='Overwrite the output file if it already exists.')
    parser.add_argument('--summarise', action='store_true', dest='summarise',
                        help='Display a summary of the data collected.')
    parser.add_argument('--ignore-removed', action='store_true', dest='ignore_removed',
                        help='Ignore cards that are not in the current version of the game.')
    default_output_path = Path(datetime.now().strftime('hsbg_card_pool-%Y%m%d-%H%M%S.json'))
    parser.set_defaults(output=default_output_path, ignore_removed=False)
    main(parser.parse_args())
