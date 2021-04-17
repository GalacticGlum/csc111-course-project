"""Make the Hearthstone Battlegrounds card pool from Hearthstone card data and a card tier dataset.

This script takes in as input a json file containing a list of every card in the game, along with
another json file containing every card in the Hearthstone Battlegrounds pool organized by tavern
tier. It outputs a new json file containing the full card information for each card in the pool.

Cards that have been removed from the game, or that do not have a tavern tier are NOT included.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def _is_battlegrounds_card(card: dict) -> bool:
    """Return whether this card is a battlegrounds card."""
    return card.get('SET', None) == 'BATTLEGROUNDS' or \
        'battlegroundsNormalDbfId' in card or \
        'battlegroundsPremiumDbfId' in card


def _is_golden(card: dict) -> bool:
    """Return whether this card is golden."""
    return 'battlegroundsNormalDbfId' in card


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    with open(args.card_data_file, encoding='utf-8') as card_data_fp,\
         open(args.pool_data_file, encoding='utf-8') as pool_data_fp:
        card_data = json.load(card_data_fp)
        pool_data = json.load(pool_data_fp)

        card_pool = {}
        for tier in pool_data:
            for card in pool_data[tier]:
                card_pool[card['name']] = card

        # Filter for only battlegrounds cards
        cards = []
        for card in card_data:
            # Filter for only battlegrounds cards
            if not _is_battlegrounds_card(card):
                continue
            name = card['name']
            # Make sure the card is in the pool.
            if name not in card_pool:
                continue
            pool_info = card_pool[name]
            # Ignore cards that don't have a tier attribute or that have been removed.
            if pool_info['is_removed'] or pool_info['tier'] is None:
                continue
            # Add tier and is_golden attributes to cards
            card['tier'] = pool_info['tier']
            card['is_golden'] = _is_golden(card)
            cards.append(card)

    with open(args.output, 'w+', encoding='utf-8') as fp:
        json.dump(cards, fp)


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
    #
    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['pathlib', 'json', 'argparse', 'datetime'],
    #     'allowed-io': ['main'],
    #     'max-line-length': 100,
    #     'disable': ['E1136', 'E9989']
    # })
    #
    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()

    parser = argparse.ArgumentParser(
        description='Make the Hearthstone Battlegrounds card pool dataset.'
    )
    parser.add_argument('card_data_file', type=Path,
                        help='A json file containing card data extracted from the Hearthstone '
                             'game client. This should match the HearthstoneJSON format.')
    parser.add_argument('pool_data_file', type=Path,
                        help='A json file containing each card organized by tavern tier. '
                             'This should match the format outputted by the '
                             'scrape_battlegrounds_pool.py script')
    parser.add_argument('-o', '--output', type=Path, default=None,
                        help='The filepath of the output json file.')
    default_output_path = Path(datetime.now().strftime('hsbg_cards-%Y%m%d-%H%M%S.json'))
    parser.set_defaults(output=default_output_path)
    main(parser.parse_args())
