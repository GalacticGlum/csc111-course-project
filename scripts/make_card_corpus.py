"""Build a corpus of textual card descriptions from Hearthstone Card data.

It is ASSUMED that the given card data json file is a list consisting of json objects,
where each object is in the format given by the HearthstoneJSON api.
"""
import json
import re
import argparse
from tqdm import tqdm
from pathlib import Path
from num2words import num2words


def clean_card_description(text: str) -> str:
    """Clean a card description."""
    text = text.replace('\n', ' ')
    text = text.replace('[x]', '')
    # Remove html tags
    text = re.sub(r'<.*?>', '', text)
    if text.endswith('.'):
        text = text[:-1]
    # Replace numbers with word representation
    text = re.sub(r'(\d+)', lambda x: num2words(int(x.group(0))), text)
    # Replace slashes with space
    text = text.replace('/', ' ')
    text = text.replace('+', ' plus ')
    # Convert to ascii
    text = text.encode('ascii', 'replace').decode('ascii').replace('?', ' ')
    return text


def capitalise_name(name: str) -> str:
    """Capitalise the first letter of the given string, and make the rest lowercase."""
    if len(name) == 0:
        return ''
    return name[0].upper() + name[1:].lower()


def normalise_name(name: str) -> str:
    """Normalise the name of a card."""
    # Replace non-alphanumeric characters with underscore
    name = re.sub(r'[^0-9a-zA-Z]+', '_', name)
    return name


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    card_data = []
    for path in args.card_data_filepaths:
        with open(path, encoding='utf-8') as fp:
            card_data.extend(json.load(fp))

    name_map = {}
    with open(args.output_filepath, 'w+', encoding='utf-8') as fp,\
            tqdm(card_data) as progress_bar:
        visited = set()
        for card in progress_bar:
            # Required attributes
            name = card.get('name', None)
            text = card.get('text', None)
            if name is None or text is None:
                continue

            # Add golden prefix
            is_golden = card.get('is_golden', False)
            if is_golden:
                name = f'{args.gold_prefix} {name}'

            # name_map[name] = normalise_name(name)
            name_map[name] = name
            name = name_map[name]

            # Manage duplicates
            if args.ignore_duplicates and name in visited:
                if args.warn_duplicates:
                    progress_bar.write(f'Ignoring duplicate: {name}')
                continue
            visited.add(name)

            # Normalise text
            card_type = card.get('type', '')
            parts = [f'{name} is a {card_type} card. {clean_card_description(text)}']
            # Optional attributes
            if (race := card.get('race', None)) is not None:
                parts += [f'{name} is a {capitalise_name(race)}']
            if (card_class := card.get('cardClass', None)) is not None:
                parts += [f'{name} is a {capitalise_name(card_class)}']
            if (rarity := card.get('rarity', None)) is not None:
                parts += [f'{name} is {capitalise_name(rarity)}']
            if (tier := card.get('tier', None)) is not None:
                parts += [f'{name} is tier {num2words(tier)}']
            if (attack := card.get('attack', None)) is not None:
                parts += [f'{name} has {num2words(attack)} attack']
            if (health := card.get('health', None)) is not None:
                parts += [f'{name} {num2words(health)} health']
            if (cost := card.get('cost', None)) is not None:
                parts += [f'{name} costs {num2words(cost)} mana']

            description = '. '.join(parts)
            fp.write(description + '\n')

    name_map_filename = args.output_filepath.with_suffix('').name + '_name_map.json'
    with open(args.output_filepath.parent / name_map_filename, 'w+') as fp:
        json.dump(name_map, fp, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make a corpus of textual card descriptions.')
    parser.add_argument('card_data_filepaths', nargs='+', type=Path,
                        help='A list of input card data json files.')
    parser.add_argument('output_filepath', type=Path, help='The output filepath.')
    parser.add_argument('--gold-prefix', type=str, default='Golden',
                        help='Prefix to add to the names of golden cards.')
    parser.add_argument('-d', '--ignore-duplicates', dest='ignore_duplicates',
                        action='store_false', help='Whether to ignore duplicate cards.')
    parser.add_argument('-w', '--warn-duplicates', dest='warn_duplicates',
                        action='store_true', help='Whether to warn about duplicate cards.')
    parser.set_defaults(ignore_duplicates=True, warn_duplicates=False)
    main(parser.parse_args())
