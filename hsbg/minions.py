"""Implementation of various minion cards.

These minions are implemented for Hearthstone Patch 20.0.
Data Source: https://hearthstone.fandom.com/wiki/Battlegrounds#Minions_by_tier

NOTE: This is a collection of all minions in the Battlegrounds pool as of Patch 20.0.
However, not all of these minions are implemented. They are merely defined here
in case that they should be implemented in the future. Pycharm will show errors, but
rest assured the file runs just fine.

Refer to the minion_list.txt file for a full list of all minions with implementations
in the Python recruitment phase simulator, and the C++ combat phase simulator.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
from __future__ import annotations
import json
import random
import logging
import argparse
from pathlib import Path
from typing import List, Set, Dict, Optional, Union

from hsbg.utils import filter_minions
from hsbg.models import CardClass, CardRarity, CardAbility, MinionRace, Buff, Minion


# The path to the list of implemented minions
MINION_LIST_PATH = Path(__file__).parent.parent / 'minion_list.txt'
with open(MINION_LIST_PATH) as fp:
    MINION_LIST = set(fp.read().splitlines())


def get_all_minions(gold_suffix: str = '_golden', whitelist: Optional[Set[str]] = None) \
        -> Dict[str, Minion]:
    """Return a dict mapping the name of each minion defined in the minions module to
    its Minion object instance.

    Each key in the returned dict is the name of a minion (with an additional suffix if the
    minion is golden, specified by the gold_suffix argument).

    Args:
        gold_suffix: The suffix to add to keys representing minions that are golden.
        whitelist: A set containing the names of minions to include.
                   If None, then all minions are included.
    """
    _ALL_MINIONS = {}
    globals_copy = globals().copy()
    for obj in globals_copy.values():
        if not isinstance(obj, Minion) or (whitelist is not None and obj.name not in whitelist):
            continue
        key = obj.name + (gold_suffix if obj.is_golden else '')

        # Warn the user if duplicate minions were found!
        if key in _ALL_MINIONS:
            logging.warn(f'Found duplicate minion (\'{key}\')')

        _ALL_MINIONS[key] = obj
    return _ALL_MINIONS


def _scan_minion_list() -> None:
    """Produces a summary of which minions are included in the minion list."""
    minions = get_all_minions()
    visited = set()
    for minion in minions.values():
        if minion.name in visited or minion.name in MINION_LIST:
            continue
        visited.add(minion.name)
        print(minion.name)
    if len(visited) == 0:
        print('All minions are in the minion list!')


def _verify_minion_list(card_json_data: Path) -> None:
    """Verify the list of implemented minions to the HearthstoneJSON API data.

    Args:
        card_json_data: Path to a json file containing card data in the
                        format given by the HearthstoneJSON data API.
    """
    with open(card_json_data, encoding='utf-8') as fp:
        card_data = json.load(fp)
        minions = get_all_minions()
        for minion in minions.values():
            try:
                entry = next(
                    x for x in card_data if x['name'] == minion.name and
                    (minion.is_golden and 'battlegroundsNormalDbfId' in x or
                     not minion.is_golden and 'battlegroundsPremiumDbfId' in x or
                     'is_golden' in x and x['is_golden'] == minion.is_golden)
                )
            except StopIteration:
                print(f'Could not find {minion.name} in \'{card_json_data}\'')
                continue

            checks = [
                minion.attack == entry['attack'],
                minion.health == entry['health'],
                minion.cost == entry['cost']
            ]
            is_valid = all(checks)
            checks_str = 'match check: attack={}, health={}, cost={}'.format(*[
                'PASSED' if x else 'FAILED' for x in checks
            ])

            if not is_valid:
                minion_type = 'golden' if minion.is_golden else 'regular'
                print(f'Error verifying {minion.name} ({minion_type}) ({checks_str})')


# A dict mapping each tier to the number of copies of each minion with that tier.
TIER_NUM_COPIES = {
    1: 18,
    2: 15,
    3: 13,
    4: 11,
    5: 9,
    6: 6
}


class MinionPool:
    """A class representing the pool of available minions."""
    # Private Instance Attributes:
    #   - _pool: A dict mapping the name of each minion to the number of copies in the pool.
    #   - _gold_suffix: The suffix used to denote gold copies of minions.
    _pool: Dict[str, int]
    _gold_suffix: str
    # Shared state variables
    __all_minions: Dict[str, Minion] = None
    __minions_below_tier: Dict[int, List[Minion]] = {}
    __pool_find_cache: Dict[int, List[Minion]] = {}

    def __init__(self, gold_suffix='_golden', force_rebuild: bool = False) -> None:
        self._pool = {}
        self._gold_suffix = gold_suffix

        # Build __all_minions if it is None, or if we are forcing a rebuild.
        if MinionPool.__all_minions is None or force_rebuild:
            MinionPool.__all_minions = get_all_minions(gold_suffix=gold_suffix)

        # Build the pool
        for minion in MinionPool.__all_minions.values():
            # Don't include unpurchasable minions or golden copies in the pool.
            if not minion.purchasable or minion.is_golden:
                continue

            copies = TIER_NUM_COPIES[minion.tier]
            self._pool[minion.name] = copies

    def find_all(self, limit: Optional[int] = None, **kwargs: dict) -> List[Minion]:
        """Find all the minions matching the given keyword arguments.
        Each keyword argument should be an attribute of the Minion class.

        Note: the returned list contains COPIES of the minions in the pool.
        """
        key = hash(frozenset(kwargs.items()))
        if key in MinionPool.__pool_find_cache:
            minions = MinionPool.__pool_find_cache[key]
        else:
            minions = filter_minions(MinionPool.__all_minions.values(), clone=False, limit=limit, **kwargs)
            MinionPool.__pool_find_cache[key] = minions

        return [x.clone() for x in minions]

    def find(self, **kwargs) -> Optional[Minion]:
        """Find the first minion matching the given keyword arguments.
        Each keyword argument should be an attribute of the Minion class.
        """
        minions = self.find_all(limit=1, **kwargs)
        return None if len(minions) == 0 else minions[0]

    def get_random(self, n: int = 1, max_tier: Optional[int] = None, remove: bool = True) \
            -> List[Minion]:
        """Return a list of random minions from the pool.

        Args:
            n: The number of minions to get.
            max_tier: The maximum tier of any minion in the returned list.
            remove: Whether to remove the minions from the pool.
            predicate: A function that takes in a minion and returns a boolean.
                       Used to filter out minions.

        >>> pool = MinionPool()
        >>> previous_pool_size = pool.size
        >>> _ = pool.get_random(remove=False)
        >>> pool.size == previous_pool_size
        True
        >>> minions = pool.get_random(n=10, max_tier=3)
        >>> all(x.tier <= 3 for x in minions)  # Test max tier
        True
        >>> pool.size == previous_pool_size - 10  # Test that minions were removed.
        True
        """
        def predicate(minion_name: str) -> bool:
            if minion_name not in MINION_LIST:
                return False

            minion = MinionPool.__all_minions[minion_name]
            return max_tier is None or minion.tier <= max_tier

        if max_tier in MinionPool.__minions_below_tier:
            pool_subset = MinionPool.__minions_below_tier[max_tier]
        else:
            pool_subset = list(filter(predicate, self._pool.keys()))
            MinionPool.__minions_below_tier[max_tier] = pool_subset

        n_copies = [self._pool[minion_name] for minion_name in pool_subset]
        minions = random.choices(pool_subset, weights=n_copies, k=n)
        if remove:
            # Remove each minion from the pool
            for minion in minions:
                self._pool[minion] = max(self._pool[minion] - 1, 0)
        # Make a clone of each minion
        return [MinionPool.__all_minions[minion].clone() for minion in minions]

    def get_golden(self, name: str) -> Minion:
        """Return a golden copy of the minion with the given name.
        Raise a ValueError if there is no minion with that name, or if it has no golden copy.
        """
        if name not in MinionPool.__all_minions:
            raise ValueError(f'Could not find minion with name \'{name}\' in the pool.')

        golden_copy_name = name + self._gold_suffix
        if golden_copy_name not in MinionPool.__all_minions:
            raise ValueError(f'The minion with name \'{name}\' has no golden copy.')

        return MinionPool.__all_minions[golden_copy_name].clone()

    def insert(self, values: Union[Minion, List[Minion]]) -> None:
        """Insert the given minions into the pool.

        >>> pool = MinionPool()
        >>> previous_pool_size = pool.size
        >>> minion = pool.find(name='Alleycat')
        >>> golden_minion = pool.find(name='Alleycat', is_golden=True)
        >>> pool.insert(minion)
        >>> pool.size == previous_pool_size + 1
        True
        >>> pool.insert(golden_minion)
        >>> pool.size == previous_pool_size + 4
        True
        """
        if isinstance(values, Minion):
            values = [values]
        for minion in values:
            if minion.name not in self._pool:
                continue
            # Add 3 regular versions of the minion, if golden.
            times = 3 if minion.is_golden else 1
            self._pool[minion.name] += times

    @property
    def size(self) -> int:
        """Return the number of minions in the pool (including copies)."""
        return sum(self._pool.values())


################################################################################
# Tier 1 cards
################################################################################
# Beast Pool

# Tabbycat summoned by Alleycat
TABBYCAT = Minion(
    'Tabbycat', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    purchasable=False
)
TABBYCAT_GOLDEN = Minion(
    'Tabbycat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    is_golden=True, purchasable=False
)

ALLEYCAT = Minion(
    'Alleycat', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.summon_minion(board.pool.find(
        name='Tabbycat', is_golden=False)
    )
)
ALLEYCAT_GOLDEN = Minion(
    'Alleycat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.summon_minion(board.pool.find(
        name='Tabbycat', is_golden=True)
    )
)

SCAVENGING_HYENA = Minion(
    'Scavenging Hyena', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    cost=2
)
SCAVENGING_HYENA_GOLDEN = Minion(
    'Scavenging Hyena', CardClass.HUNTER, MinionRace.BEAST, 4, 4,
    cost=2, is_golden=True
)

# Demon Pool
FIENDISH_SERVANT = Minion(
    'Fiendish Servant', CardClass.WARLOCK, MinionRace.DEMON, 2, 1,
    abilities=CardAbility.DEATH_RATTLE
)
FIENDISH_SERVANT_GOLDEN = Minion(
    'Fiendish Servant', CardClass.WARLOCK, MinionRace.DEMON, 4, 2,
    is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

VULGAR_HOMUNCULUS = Minion(
    'Vulgar Homunculus', CardClass.WARLOCK, MinionRace.DEMON, 2, 4,
    cost=2, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.attack_hero(2)
)
VULGAR_HOMUNCULUS_GOLDEN = Minion(
    'Vulgar Homunculus', CardClass.WARLOCK, MinionRace.DEMON, 4, 8,
    cost=2, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.attack_hero(2)
)


def _wrath_weaver_on_any_played(self: Minion, board: TavernGameBoard,
                                played_minion: Minion) -> None:
    """Handle the effect for the Wrath Weaver minion when a card is played from the hand.
    Effect: After you play a demon, deal 1 damage to your hero, and gain +2/+2 (or +4/+4 if golden).
    """
    if MinionRace.DEMON not in played_minion.race:
        return
    if self.is_golden:
        buff = Buff(4, 4, CardAbility.NONE)
    else:
        buff = Buff(2, 2, CardAbility.NONE)

    self.add_buff(buff)
    board.attack_hero(1)


WRATH_WEAVER = Minion(
    'Wrath Weaver', CardClass.NEUTRAL, MinionRace.NONE, 1, 3,
    _on_any_played=_wrath_weaver_on_any_played
)
WRATH_WEAVER_GOLDEN = Minion(
    'Wrath Weaver', CardClass.NEUTRAL, MinionRace.NONE, 2, 6,
    is_golden=True,
    _on_any_played=_wrath_weaver_on_any_played
)

# Dragon Pool
DRAGON_SPAWN_LIEUTENANT = Minion(
    'Dragonspawn Lieutenant', CardClass.NEUTRAL, MinionRace.DRAGON, 2, 3,
    cost=2, abilities=CardAbility.TAUNT
)
DRAGON_SPAWN_LIEUTENANT_GOLDEN = Minion(
    'Dragonspawn Lieutenant', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 6,
    cost=2, is_golden=True, abilities=CardAbility.TAUNT
)

RED_WHELP = Minion(
    'Red Whelp', CardClass.NEUTRAL, MinionRace.DRAGON, 1, 2
)
RED_WHELP_GOLDEN = Minion(
    'Red Whelp', CardClass.NEUTRAL, MinionRace.DRAGON, 2, 4,
    is_golden=True
)

# Elemental Pool
REFRESHING_ANOMALY = Minion(
    'Refreshing Anomaly', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 1, 3,
    abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.set_refresh_cost(0, times=1)
)
REFRESHING_ANOMALY_GOLDEN = Minion(
    'Refreshing Anomaly', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 6,
    is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.set_refresh_cost(0, times=2)
)

# Water Droplet generated by Sellemental
WATER_DROPLET = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, purchasable=False
)
WATER_DROPLET_GOLDEN = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=3, is_golden=True, purchasable=False
)


def _sellemental_on_this_sold(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Sellemental minion.
    Effect: When you sell this, add a 2/2 Elemental to your hand (or 2 if golden).
    """
    n = 2 if self.is_golden else 1
    minion = board.pool.find(name='Water Droplet')
    for _ in range(n):
        board.add_minion_to_hand(minion)


SELLEMENTAL = Minion(
    'Sellemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3,
    _on_this_sold=_sellemental_on_this_sold
)
SELLEMENTAL_GOLDEN = Minion(
    'Sellemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=3, is_golden=True,
    _on_this_sold=_sellemental_on_this_sold
)

# Mech Pool
MICRO_MACHINE = Minion(
    'Micro Machine', CardClass.NEUTRAL, MinionRace.MECH, 1, 2,
    cost=2,
    _on_new_turn=lambda self, board: self.add_buff(Buff(1, 0, CardAbility.NONE))
)
MICRO_MACHINE_GOLDEN = Minion(
    'Micro Machine', CardClass.NEUTRAL, MinionRace.MECH, 2, 4,
    cost=2, is_golden=True,
    _on_new_turn=lambda self, board: self.add_buff(Buff(2, 0, CardAbility.NONE))
)


def _micro_mummy_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the Micro Mummy effect on the end of a turn.
    Effect: At the end of your turn, give another random friendly
    minion +1 (or +2 if golden) Attack.
    """
    minion = board.get_random_minion_on_board(ignore=[self])
    if minion is None:
        return
    if self.is_golden:
        minion.add_buff(Buff(2, 0, CardAbility.NONE))
    else:
        minion.add_buff(Buff(1, 0, CardAbility.NONE))


MICRO_MUMMY = Minion(
    'Micro Mummy', CardClass.PALADIN, MinionRace.MECH, 1, 2,
    cost=2, rarity=CardRarity.EPIC, abilities=CardAbility.REBORN,
    _on_end_turn=_micro_mummy_on_end_turn
)
MICRO_MUMMY_GOLDEN = Minion(
    'Micro Mummy', CardClass.PALADIN, MinionRace.MECH, 2, 4,
    cost=2, rarity=CardRarity.EPIC, is_golden=True, abilities=CardAbility.REBORN,
    _on_end_turn=_micro_mummy_on_end_turn
)


# Murloc Pool
def _murloc_tidecaller_on_any_summoned(self: Minion, board: TavernGameBoard,
                                       summoned_minion: Minion) -> None:
    """Handle the Murloc Tidecaller effect.
    Effect: Whenever you summon a Murloc, gain +1 (or +2 if golden) Attack."""
    if MinionRace.MURLOC not in summoned_minion.race:
        return
    if self.is_golden:
        self.add_buff(Buff(2, 0, CardAbility.NONE))
    else:
        self.add_buff(Buff(1, 0, CardAbility.NONE))


MURLOC_TIDECALLER = Minion(
    'Murloc Tidecaller', CardClass.NEUTRAL, MinionRace.MURLOC, 1, 2,
    rarity=CardRarity.RARE,
    _on_any_summoned=_murloc_tidecaller_on_any_summoned
)
MURLOC_TIDECALLER_GOLDEN = Minion(
    'Murloc Tidecaller', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 4,
    rarity=CardRarity.RARE, is_golden=True,
    _on_any_summoned=_murloc_tidecaller_on_any_summoned
)

# Murloc Scout summoned by Murloc Tidehunter
MURLOC_SCOUT = Minion(
    'Murloc Scout', CardClass.NEUTRAL, MinionRace.MURLOC, 1, 1,
    purchasable=False
)
MURLOC_SCOUT_GOLDEN = Minion(
    'Murloc Scout', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 2,
    purchasable=False, is_golden=True
)

MURLOC_TIDEHUNTER = Minion(
    'Murloc Tidehunter', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 1,
    cost=2, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.summon_minion(board.pool.find(
        name='Murloc Scout', is_golden=False)
    )
)
MURLOC_TIDEHUNTER_GOLDEN = Minion(
    'Murloc Tidehunter', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 2,
    cost=2, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda _, board: board.summon_minion(board.pool.find(
        name='Murloc Scout', is_golden=True)
    )
)


def _rockpool_hunter_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the Rockpool Hunter battlecry effect.
    Effect: Give a friendly Murloc +1/+1 (or +2/+2 if golden).

    Note: the murloc is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Murloc
    minion = board.get_random_minion_on_board(race=MinionRace.MURLOC, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))
    else:
        minion.add_buff(Buff(1, 1, CardAbility.NONE))


ROCKPOOL_HUNTER = Minion(
    'Rockpool Hunter', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 3,
    cost=2, abilities=CardAbility.BATTLECRY,
    _on_this_played=_rockpool_hunter_on_this_played
)
ROCKPOOL_HUNTER_GOLDEN = Minion(
    'Rockpool Hunter', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 6,
    cost=2, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_rockpool_hunter_on_this_played
)


# Pirate Pool
def _deck_swabbie_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the Deck Swabbie battlecry effect.
    Effect: Reduce the cost of upgrading Bob's Tavern by (1) (or (2) if golden).
    """
    discount = 2 if self.is_golden else 1
    board.set_tavern_upgrade_discount(discount, times=1)


DECK_SWABBIE = Minion(
    'Deck Swabbie', CardClass.NEUTRAL, MinionRace.PIRATE, 2, 2,
    cost=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_deck_swabbie_on_this_played
)
DECK_SWABBIE_GOLDEN = Minion(
    'Deck Swabbie', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 4,
    cost=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_deck_swabbie_on_this_played
)

SCALLYWAG = Minion(
    'Scallywag', CardClass.NEUTRAL, MinionRace.PIRATE, 2, 1,
    abilities=CardAbility.DEATH_RATTLE
)
SCALLYWAG_GOLDEN = Minion(
    'Scallywag', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 2,
    is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# Neutral Pool
ACOLYTE_OF_CTHUN = Minion(
    'Acolyte of C\'Thun', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 2,
    abilities=CardAbility.TAUNT | CardAbility.REBORN
)
ACOLYTE_OF_CTHUN_GOLDEN = Minion(
    'Acolyte of C\'Thun', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 4,
    is_golden=True, abilities=CardAbility.TAUNT | CardAbility.REBORN
)


################################################################################
# Tier 2 cards
################################################################################
BIG_BAD_WOLF = Minion(
    'Big Bad Wolf', CardClass.HUNTER, MinionRace.BEAST, 3, 2,
    cost=2, tier=1
)
BIG_BAD_WOLF_GOLDEN = Minion(
    'Big Bad Wolf', CardClass.HUNTER, MinionRace.BEAST, 6, 4,
    cost=2, tier=1, is_golden=True
)

KINDLY_GRANDMOTHER = Minion(
    'Kindly Grandmother', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    cost=2, tier=2, abilities=CardAbility.DEATH_RATTLE
)
KINDLY_GRANDMOTHER_GOLDEN = Minion(
    'Kindly Grandmother', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    cost=2, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)


def _pack_leader_on_any_summoned(self: Minion, board: TavernGameBoard,
                                 summoned_minion: Minion) -> None:
    """Handle the Pack Leader effect.
    Effect: Whenever you summon a Beast, give it +2 (or +4 if golden) Attack.
    """
    if MinionRace.BEAST not in summoned_minion.race:
        return
    if self.is_golden:
        summoned_minion.add_buff(Buff(4, 0, CardAbility.NONE))
    else:
        summoned_minion.add_buff(Buff(2, 0, CardAbility.NONE))


PACK_LEADER = Minion(
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 3, 3,
    cost=2, tier=2, rarity=CardRarity.RARE,
    _on_any_summoned=_pack_leader_on_any_summoned
)
PACK_LEADER_GOLDEN = Minion(
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 6, 6,
    cost=2, tier=2, rarity=CardRarity.RARE, is_golden=True,
    _on_any_summoned=_pack_leader_on_any_summoned
)


def _rabid_saurolisk_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the Rabid Saurolisk effect.
    Effect: After you play a minion with Deathrattle, gain +1/+2 (or +2/+4 if golden).
    """
    if CardAbility.DEATH_RATTLE not in played_minion.abilities:
        return
    if self.is_golden:
        self.add_buff(Buff(2, 4, CardAbility.NONE))
    else:
        self.add_buff(Buff(1, 2, CardAbility.NONE))


RABID_SAUROLISK = Minion(
    'Rabid Saurolisk', CardClass.HUNTER, MinionRace.BEAST, 3, 2,
    cost=3, tier=2,
    _on_any_played=_rabid_saurolisk_on_any_played
)
RABID_SAUROLISK_GOLDEN = Minion(
    'Rabid Saurolisk', CardClass.HUNTER, MinionRace.BEAST, 6, 4,
    cost=3, tier=2, is_golden=True,
    _on_any_played=_rabid_saurolisk_on_any_played
)

# Demon Pool

# Imp summoned by Imp Gang Boss and Imprisoner
IMP = Minion(
    'Imp', CardClass.WARLOCK, MinionRace.DEMON, 1, 1,
    tier=1, purchasable=False
)
IMP_GOLDEN = Minion(
    'Imp', CardClass.WARLOCK, MinionRace.DEMON, 2, 2,
    tier=1, is_golden=True, purchasable=False
)

IMPRISONER = Minion(
    'Imprisoner', CardClass.NEUTRAL, MinionRace.DEMON, 3, 3,
    cost=3, tier=2, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)
IMPRISONER_GOLDEN = Minion(
    'Imprisoner', CardClass.NEUTRAL, MinionRace.DEMON, 6, 6,
    cost=3, tier=2, is_golden=True,
    abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)


def _nathrezim_overseer_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the Nathrezim Overseer battlecry effect.
    Effect: Give a friendly Demon +2/+2 (or +4/+4 if golden).

    Note: the demon is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Demon
    minion = board.get_random_minion_on_board(race=MinionRace.DEMON, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))


NATHREZIM_OVERSEER = Minion(
    'Nathrezim Overseer', CardClass.NEUTRAL, MinionRace.DEMON, 2, 3,
    cost=3, tier=2, rarity=CardRarity.RARE, abilities=CardAbility.BATTLECRY,
    _on_this_played=_nathrezim_overseer_on_this_played
)
NATHREZIM_OVERSEER_GOLDEN = Minion(
    'Nathrezim Overseer', CardClass.NEUTRAL, MinionRace.DEMON, 4, 6,
    cost=3, tier=2, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.BATTLECRY,
    _on_this_played=_nathrezim_overseer_on_this_played
)

# Dragon Pool
GLYPH_GUARDIAN = Minion(
    'Glyph Guardian', CardClass.MAGE, MinionRace.DRAGON, 2, 4,
    cost=3, tier=2
)
GLYPH_GUARDIAN_GOLDEN = Minion(
    'Glyph Guardian', CardClass.MAGE, MinionRace.DRAGON, 4, 8,
    cost=3, tier=2, is_golden=True
)


def _steward_of_time_on_this_sold(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Steward of Time minion.
    Effect: When you sell this minion, give all minions in Bob's Tavern +1/+1 (or +2/+2 if golden).
    """
    for minion in board.get_minions_on_board():
        if self.is_golden:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))
        else:
            minion.add_buff(Buff(1, 1, CardAbility.NONE))


STEWARD_OF_TIME = Minion(
    'Steward of Time', CardClass.NEUTRAL, MinionRace.DRAGON, 3, 4,
    cost=4, tier=2,
    _on_this_sold=_steward_of_time_on_this_sold
)
STEWARD_OF_TIME_GOLDEN = Minion(
    'Steward of Time', CardClass.NEUTRAL, MinionRace.DRAGON, 6, 8,
    cost=4, tier=2, is_golden=True,
    _on_this_sold=_steward_of_time_on_this_sold
)

WAXRIDER_TOGWAGGLE = Minion(
    'Waxrider Togwaggle', CardClass.NEUTRAL, MinionRace.NONE, 1, 3,
    cost=3, tier=2
)
WAXRIDER_TOGWAGGLE_GOLDEN = Minion(
    'Waxrider Togwaggle', CardClass.NEUTRAL, MinionRace.NONE, 2, 6,
    cost=3, tier=2, is_golden=True
)


# Elemental Pool
def _molten_rock_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the effect for the Molten Rock minion.
    Effect: After you play an Elemental, gain +1 (or +2 if golden) Health.
    """
    if played_minion is self or MinionRace.ELEMENTAL not in played_minion.race:
        return
    if self.is_golden:
        self.add_buff(Buff(0, 2, CardAbility.NONE))
    else:
        self.add_buff(Buff(0, 1, CardAbility.NONE))


MOLTEN_ROCK = Minion(
    'Molten Rock', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 4,
    cost=3, tier=2, abilities=CardAbility.TAUNT,
    _on_any_played=_molten_rock_on_any_played
)
MOLTEN_ROCK_GOLDEN = Minion(
    'Molten Rock', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 8,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.TAUNT,
    _on_any_played=_molten_rock_on_any_played
)


def _party_elemental_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the effect for the Party Elemental minion.
    Effect: After you play an Elemental, give another random friendly Elemental +1/+1
    (or +2/+2 if golden).

    Note: the elemental is chosen RANDOMLY since we do not have targetting implemented.
    """
    if played_minion is self or MinionRace.ELEMENTAL not in played_minion.race:
        return

    times = 2 if self.is_golden else 1
    for _ in range(times):
        minion = board.get_random_minion_on_board(race=MinionRace.ELEMENTAL, ignore=[played_minion])
        if minion is None:
            return
        # Give +1/+1
        minion.add_buff(Buff(1, 1, CardAbility.NONE))


PARTY_ELEMENTAL = Minion(
    'Party Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 3, 2,
    cost=4, tier=2,
    _on_any_played=_party_elemental_on_any_played
)
PARTY_ELEMENTAL_GOLDEN = Minion(
    'Party Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 6, 4,
    cost=4, tier=2, is_golden=True,
    _on_any_played=_party_elemental_on_any_played
)

# Mech Pool
DAMAGED_GOLEM = Minion(
    'Damaged Golem', CardClass.NEUTRAL, MinionRace.MECH, 2, 1,
    cost=1, tier=1
)
DAMAGED_GOLEM_GOLDEN = Minion(
    'Damaged Golem', CardClass.NEUTRAL, MinionRace.MECH, 4, 2,
    cost=1, tier=1, is_golden=True
)

HARVEST_GOLEM = Minion(
    'Harvest Golem', CardClass.NEUTRAL, MinionRace.MECH, 2, 3,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
HARVEST_GOLEM_GOLDEN = Minion(
    'Harvest Golem', CardClass.NEUTRAL, MinionRace.MECH, 4, 6,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

KABOOM_BOT = Minion(
    'Kaboom Bot', CardClass.NEUTRAL, MinionRace.MECH, 2, 2,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
KABOOM_BOT_GOLDEN = Minion(
    'Kaboom Bot', CardClass.NEUTRAL, MinionRace.MECH, 4, 4,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)


def _metaltooth_leaper_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Metaltooth Leaper minion.
    Effect: Give your other Mechs +2 (or +4 if golden) Attack.
    """
    additional_attack = 4 if self.is_golden else 2
    minions = board.get_minions_on_board(race=MinionRace.MECH, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(additional_attack, 0, CardAbility.NONE))


METALTOOTH_LEAPER = Minion(
    'Metaltooth Leaper', CardClass.HUNTER, MinionRace.MECH, 3, 3,
    cost=3, tier=2, abilities=CardAbility.BATTLECRY,
    _on_this_played=_metaltooth_leaper_on_this_played
)
METALTOOTH_LEAPER_GOLDEN = Minion(
    'Metaltooth Leaper', CardClass.HUNTER, MinionRace.MECH, 6, 6,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_metaltooth_leaper_on_this_played
)

# Murloc Pool
MURLOC_WARLEADER = Minion(
    'Murloc Warleader', CardClass.NEUTRAL, MinionRace.MURLOC, 3, 3,
    cost=3, tier=2
)
MURLOC_WARLEADER_GOLDEN = Minion(
    'Murloc Warleader', CardClass.NEUTRAL, MinionRace.MURLOC, 6, 6,
    cost=3, tier=2, is_golden=True
)

OLD_MURK_EYE = Minion(
    'Old Murk-Eye', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 4,
    cost=4, tier=2, rarity=CardRarity.LEGENDARY
)
OLD_MURK_EYE_GOLDEN = Minion(
    'Old Murk-Eye', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 8,
    cost=4, tier=2, rarity=CardRarity.LEGENDARY, is_golden=True
)

# Pirate Pool
FREEDEALING_GAMBLER = Minion(
    'Freedealing Gambler', CardClass.NEUTRAL, MinionRace.PIRATE, 3, 3,
    cost=3, tier=2,
    # Effect: This minion sells for 3 golds.
    _on_this_sold=lambda _, board: board.give_gold(abs(3 - board._minion_sell_price))
)
FREEDEALING_GAMBLER_GOLDEN = Minion(
    'Freedealing Gambler', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=3, tier=2, is_golden=True,
    # Effect: This minion sells for 6 golds.
    _on_this_sold=lambda _, board: board.give_gold(abs(6 - board._minion_sell_price))
)

SOUTHSEA_CAPTAIN = Minion(
    'Southsea Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 3, 3,
    cost=3, tier=2, rarity=CardRarity.EPIC
)
SOUTHSEA_CAPTAIN_GOLDEN = Minion(
    'Southsea Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=3, tier=2, rarity=CardRarity.EPIC, is_golden=True
)

YO_HO_OGRE = Minion(
    'Yo-Ho-Ogre', CardClass.NEUTRAL, MinionRace.PIRATE, 2, 6,
    cost=6, tier=2, abilities=CardAbility.TAUNT
)
YO_HO_OGRE_GOLDEN = Minion(
    'Yo-Ho-Ogre', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 12,
    cost=6, tier=2, is_golden=True, abilities=CardAbility.TAUNT
)


# Neutral Pool
def _managerie_mug_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Menagerie Mug minion.
    Effect: Give 3 random friendly minions of different minion types +1/+1 (or +2/+2 if golden).
    """
    minions_by_race = {}
    for minion in board.get_minions_on_board(ignore=[self]):
        if minion.race not in minions_by_race:
            minions_by_race[minion.race] = []
        minions_by_race[minion.race].append(minion)

    keys = random.sample(list(minions_by_race.keys()), k=min(3, len(minions_by_race)))
    for key in keys:
        minion = random.choice(minions_by_race[key])
        if self.is_golden:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))
        else:
            minion.add_buff(Buff(1, 1, CardAbility.NONE))


MENAGERIE_MUG = Minion(
    'Menagerie Mug', CardClass.NEUTRAL, MinionRace.NONE, 2, 2,
    cost=3, tier=2, abilities=CardAbility.BATTLECRY,
    _on_this_played=_managerie_mug_on_this_played
)
MENAGERIE_MUG_GOLDEN = Minion(
    'Menagerie Mug', CardClass.NEUTRAL, MinionRace.NONE, 4, 4,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_managerie_mug_on_this_played
)

SPAWN_OF_NZOTH = Minion(
    'Spawn of N\'Zoth', CardClass.NEUTRAL, MinionRace.NONE, 2, 2,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
SPAWN_OF_NZOTH_GOLDEN = Minion(
    'Spawn of N\'Zoth', CardClass.NEUTRAL, MinionRace.NONE, 4, 4,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

SELFLESS_HERO = Minion(
    'Selfless Hero', CardClass.PALADIN, MinionRace.NONE, 2, 1,
    cost=1, tier=2, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE
)
SELFLESS_HERO_GOLDEN = Minion(
    'Selfless Hero', CardClass.PALADIN, MinionRace.NONE, 4, 2,
    cost=1, tier=2, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

TORMENETED_RITUALIST = Minion(
    'Tormented Ritualist', CardClass.NEUTRAL, MinionRace.NONE, 2, 3,
    cost=3, tier=2, abilities=CardAbility.TAUNT
)
TORMENETED_RITUALIST_GOLDEN = Minion(
    'Tormented Ritualist', CardClass.NEUTRAL, MinionRace.NONE, 4, 6,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.TAUNT
)

UNSTABLE_GHOUL = Minion(
    'Unstable Ghoul', CardClass.NEUTRAL, MinionRace.NONE, 1, 3,
    cost=2, tier=2, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)
UNSTABLE_GHOUL_GOLDEN = Minion(
    'Unstable Ghoul', CardClass.NEUTRAL, MinionRace.NONE, 2, 6,
    cost=2, tier=2, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

################################################################################
# Tier 3 cards
################################################################################
# Beast Pool

# Spider summoned by Infested Wolf
SPIDER = Minion(
    'Spider', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    tier=1, purchasable=False
)
SPIDER_GOLDEN = Minion(
    'Spider', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    tier=1, is_golden=True, purchasable=False
)

INFESTED_WOLF = Minion(
    'Infested Wolf', CardClass.HUNTER, MinionRace.BEAST, 3, 3,
    cost=4, tier=3, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE
)
INFESTED_WOLF_GOLDEN = Minion(
    'Infested Wolf', CardClass.HUNTER, MinionRace.BEAST, 6, 6,
    cost=4, tier=3, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE
)

MONSTROUS_MACAW = Minion(
    'Monstrous Macaw', CardClass.NEUTRAL, MinionRace.BEAST, 4, 3,
    cost=3, tier=3
)
MONSTROUS_MACAW_GOLDEN = Minion(
    'Monstrous Macaw', CardClass.NEUTRAL, MinionRace.BEAST, 8, 6,
    cost=3, tier=3, is_golden=True
)


def _houndmaster_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Houndmaster minion.
    Effect: Give a friendly Beast +2/+2 (or +4/+4 if golden) and Taunt.

    Note: the beast is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Beast
    minion = board.get_random_minion_on_board(race=MinionRace.BEAST, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.TAUNT))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.TAUNT))


HOUNDMASTER = Minion(
    'Houndmaster', CardClass.HUNTER, MinionRace.NONE, 4, 3,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_houndmaster_on_this_played
)
HOUNDMASTER_GOLDEN = Minion(
    'Houndmaster', CardClass.HUNTER, MinionRace.NONE, 8, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_houndmaster_on_this_played
)

# Rat summoned by Rat Pack
RAT = Minion(
    'Rat', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    tier=1, purchasable=False
)
RAT_GOLDEN = Minion(
    'Rat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    tier=1, is_golden=True, purchasable=False
)

RAT_PACK = Minion(
    'Rat Pack', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    cost=3, tier=3, rarity=CardRarity.EPIC,
    abilities=CardAbility.DEATH_RATTLE
)
RAT_PACK_GOLDEN = Minion(
    'Rat Pack', CardClass.HUNTER, MinionRace.BEAST, 4, 4,
    cost=3, tier=3, rarity=CardRarity.EPIC, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE
)

# Demon Pool
IMP_GANG_BOSS = Minion(
    'Imp Gang Boss', CardClass.WARLOCK, MinionRace.DEMON, 2, 4,
    cost=3, tier=3
)
IMP_GANG_BOSS_GOLDEN = Minion(
    'Imp Gang Boss', CardClass.WARLOCK, MinionRace.DEMON, 4, 8,
    cost=3, tier=3, is_golden=True
)


def _crystal_weaver_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Crystalweaver minion.
    Effect: Give your Demons +1/+1 (or +2/+2 if golden).
    """
    minions = board.get_minions_on_board(race=MinionRace.DEMON)
    for minion in minions:
        if self.is_golden:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))
        else:
            minion.add_buff(Buff(1, 1, CardAbility.NONE))


CRYSTAL_WEAVER = Minion(
    'Crystalweaver', CardClass.WARLOCK, MinionRace.NONE, 5, 4,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_crystal_weaver_on_this_played
)
CRYSTAL_WEAVER_GOLDEN = Minion(
    'Crystalweaver', CardClass.WARLOCK, MinionRace.NONE, 10, 8,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_crystal_weaver_on_this_played
)


def _soul_devourer_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Soul Devourer minion.
    Effect (regular): Choose a friendly Demon. Remove it to gain its stats and 3 gold.
    Effect (golden):  Choose a friendly Demon. Remove it to gain double its stats and 6 gold.
    """
    multiplier = 2 if self.is_golden else 1
    # Give gold
    board.give_gold(3 * multiplier)

    minion = board.get_random_minion_on_board(race=MinionRace.DEMON, ignore=[self])
    if minion is None:
        # There is no friendly Demon minion.
        return
    # Remove minion from board
    board.remove_minion_from_board(board.get_index_of_minion_on_board(minion))

    attack_buff = minion.current_attack * multiplier
    health_buff = minion.current_health * multiplier

    # Give stats to self
    self.add_buff(Buff(attack_buff, health_buff, CardAbility.NONE))


SOUL_DEVOURER = Minion(
    'Soul Devourer', CardClass.NEUTRAL, MinionRace.DEMON, 3, 3,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_soul_devourer_on_this_played
)
SOUL_DEVOURER_GOLDEN = Minion(
    'Soul Devourer', CardClass.NEUTRAL, MinionRace.DEMON, 6, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_soul_devourer_on_this_played
)

SOUL_JUGGLER = Minion(
    'Soul Juggler', CardClass.WARLOCK, MinionRace.NONE, 3, 3,
    cost=3, tier=3
)
SOUL_JUGGLER_GOLDEN = Minion(
    'Soul Juggler', CardClass.WARLOCK, MinionRace.NONE, 6, 6,
    cost=3, tier=3, is_golden=True
)

# Dragon Pool
BRONZE_WARDEN = Minion(
    'Bronze Warden', CardClass.NEUTRAL, MinionRace.DRAGON, 2, 1,
    cost=4, tier=3, abilities=CardAbility.DIVINE_SHIELD | CardAbility.REBORN
)
BRONZE_WARDEN_GOLDEN = Minion(
    'Bronze Warden', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 2,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DIVINE_SHIELD | CardAbility.REBORN
)


def _hangry_dragon_on_new_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Hangry Dragon minion.
    Effect: At the start of your turn, gain +2/+2 (or +4/+4 if golden) if you won the last combat.
    """
    if not board.won_previous:
        return

    if self.is_golden:
        self.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        self.add_buff(Buff(2, 2, CardAbility.NONE))


HANGRY_DRAGON = Minion(
    'Hangry Dragon', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 4,
    cost=5, tier=3,
    _on_new_turn=_hangry_dragon_on_new_turn
)
HANGRY_DRAGON_GOLDEN = Minion(
    'Hangry Dragon', CardClass.NEUTRAL, MinionRace.DRAGON, 8, 8,
    cost=5, tier=3, is_golden=True,
    _on_new_turn=_hangry_dragon_on_new_turn
)


def _twilight_emissary_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Twilight Emissary minion.
    Effect: Give a friendly Dragon +2/+2 (or +4/+4 if golden).

    Note: the dragon is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Murloc
    minion = board.get_random_minion_on_board(race=MinionRace.DRAGON, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))


TWILIGHT_EMISSARY = Minion(
    'Twilight Emissary', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 4,
    cost=6, tier=3, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=_twilight_emissary_on_this_played
)
TWILIGHT_EMISSARY_GOLDEN = Minion(
    'Twilight Emissary', CardClass.NEUTRAL, MinionRace.DRAGON, 8, 8,
    cost=6, tier=3, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=_twilight_emissary_on_this_played
)


# Elemental Pool
def _arcane_assistant_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Arcane Assistant minion.
    Effect: Give your Elementals +1/+1 (or +2/+2 if golden).
    """
    buff_amount = 2 if self.is_golden else 1
    minions = board.get_minions_on_board(race=MinionRace.ELEMENTAL, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(buff_amount, buff_amount, CardAbility.NONE))


ARCANE_ASSISTANT = Minion(
    'Arcane Assistant', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 3, 3,
    cost=3, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_arcane_assistant_on_this_played
)
ARCANE_ASSISTANT_GOLDEN = Minion(
    'Arcane Assistant', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 6, 6,
    cost=3, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_arcane_assistant_on_this_played
)

CRACKLING_CYCLONE = Minion(
    'Crackling Cyclone', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 1,
    cost=4, tier=3, abilities=CardAbility.DIVINE_SHIELD | CardAbility.WINDFURY
)
CRACKLING_CYCLONE_GOLDEN = Minion(
    'Crackling Cyclone', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 8, 2,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DIVINE_SHIELD | CardAbility.MEGA_WINDFURY
)

# NOTE: Stasis Elemental adds a card to the list of recruits when it is played.
#       This can be problematic when we already have the maximum number of recruits,
#       since this would cause the number of available recruits to exceed the maximum,
#       which the state space representation of the game does not support (we always assume the
#       number of recruits is capped at the maximum, and we pad the state accordingly).
#
#       As a result, we probably won't implement this card. But, it is here for reference.
STASIS_ELEMENTAL = Minion(
    'Stasis Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY
)
STASIS_ELEMENTAL_GOLDEN = Minion(
    'Stasis Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 8, 8,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY
)

# Mech Pool
DEFLECT_O_BOT = Minion(
    'Deflect-o-Bot', CardClass.NEUTRAL, MinionRace.MECH, 3, 2,
    cost=4, tier=3, abilities=CardAbility.DIVINE_SHIELD
)
DEFLECT_O_BOT_GOLDEN = Minion(
    'Deflect-o-Bot', CardClass.NEUTRAL, MinionRace.MECH, 6, 4,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DIVINE_SHIELD
)


def _iron_sensei_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Iron Sensei minion.
    Effect: At the end of your turn, give another friendly Mech +2/+2 (or +4/+4 if golden).

    Note: the mech is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Mech
    minion = board.get_random_minion_on_board(race=MinionRace.MECH, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))


IRON_SENSEI = Minion(
    'Iron Sensei', CardClass.ROGUE, MinionRace.MECH, 2, 2,
    cost=3, tier=3, rarity=CardRarity.RARE,
    _on_end_turn=_iron_sensei_on_end_turn
)
IRON_SENSEI_GOLDEN = Minion(
    'Iron Sensei', CardClass.ROGUE, MinionRace.MECH, 4, 4,
    cost=3, tier=3, rarity=CardRarity.RARE, is_golden=True,
    _on_end_turn=_iron_sensei_on_end_turn
)

PILOTED_SHREDDER = Minion(
    'Piloted Shredder', CardClass.NEUTRAL, MinionRace.MECH, 4, 3,
    cost=4, tier=3, abilities=CardAbility.DEATH_RATTLE
)
PILOTED_SHREDDER_GOLDEN = Minion(
    'Piloted Shredder', CardClass.NEUTRAL, MinionRace.MECH, 8, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)


def _screwjank_clunker_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Screwjank Clunker minion.
    Effect: Give a friendly Mech +2/+2 (or +4/+4 if golden).

    Note: the mech is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Mech
    minion = board.get_random_minion_on_board(race=MinionRace.MECH, ignore=[self])
    if minion is None:
        return

    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))


SCREWJANK_CLUNKER = Minion(
    'Screwjank Clunker', CardClass.WARRIOR, MinionRace.MECH, 2, 5,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_screwjank_clunker_on_this_played
)
SCREWJANK_CLUNKER_GOLDEN = Minion(
    'Screwjank Clunker', CardClass.WARRIOR, MinionRace.MECH, 4, 10,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_screwjank_clunker_on_this_played
)

# Microbot summoned by Replicating Menace
MICROBOT = Minion(
    'Microbot', CardClass.NEUTRAL, MinionRace.MECH, 1, 1,
    tier=1, purchasable=False
)
MICROBOT_GOLDEN = Minion(
    'Microbot', CardClass.NEUTRAL, MinionRace.MECH, 2, 2,
    tier=1, is_golden=True, purchasable=False
)

REPLICATING_MENACE = Minion(
    'Replicating Menace', CardClass.NEUTRAL, MinionRace.MECH, 3, 1,
    cost=4, tier=3, abilities=CardAbility.DEATH_RATTLE
)
REPLICATING_MENACE_GOLDEN = Minion(
    'Replicating Menace', CardClass.NEUTRAL, MinionRace.MECH, 6, 2,
    cost=4, tier=3, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE
)


# Murloc Pool
def _coldlight_seer_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Coldlight Seer minion.
    Effect: Give your other Murlocs +2 (or +4 if golden) health.
    """
    additional_health = 4 if self.is_golden else 2
    minions = board.get_minions_on_board(race=MinionRace.MURLOC, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(0, additional_health, CardAbility.NONE))


COLDLIGHT_SEER = Minion(
    'Coldlight Seer', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 3,
    cost=3, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_coldlight_seer_on_this_played
)
COLDLIGHT_SEER_GOLDEN = Minion(
    'Coldlight Seer', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 6,
    cost=3, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_coldlight_seer_on_this_played
)


def _felfin_navigator_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Felfin Navigator minion.
    Effect: Give your other Murlocs +1/+1 (or +2/+2 if golden).
    """
    buff_amount = 2 if self.is_golden else 1
    minions = board.get_minions_on_board(race=MinionRace.MURLOC, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(buff_amount, buff_amount, CardAbility.NONE))


FELFIN_NAVIGATOR = Minion(
    'Felfin Navigator', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 4,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_felfin_navigator_on_this_played
)
FELFIN_NAVIGATOR_GOLDEN = Minion(
    'Felfin Navigator', CardClass.NEUTRAL, MinionRace.MURLOC, 8, 8,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_felfin_navigator_on_this_played
)


# Pirate Pool
def _bloodsail_cannoneer_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Bloodsail Cannoneer minion.
    Effect: Give your other Pirates +3 (or +6 if golden) Attack.
    """
    additional_attack = 6 if self.is_golden else 3
    minions = board.get_minions_on_board(race=MinionRace.PIRATE, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(additional_attack, 0, CardAbility.NONE))


BLOODSAIL_CANNONEER = Minion(
    'Bloodsail Cannoneer', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 3,
    cost=4, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_bloodsail_cannoneer_on_this_played
)
BLOODSAIL_CANNONEER_GOLDEN = Minion(
    'Bloodsail Cannoneer', CardClass.NEUTRAL, MinionRace.PIRATE, 8, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_bloodsail_cannoneer_on_this_played
)


def _salty_looter_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the effect for the Salty Looter minion when a card is played from the hand.
    Effect: Whenever you play a Pirate, gain +1/+1 (or +2/+2 if golden).
    """
    if played_minion is self or MinionRace.PIRATE not in played_minion.race:
        return
    if self.is_golden:
        self.add_buff(Buff(2, 2, CardAbility.NONE))
    else:
        self.add_buff(Buff(1, 1, CardAbility.NONE))


SALTY_LOOTER = Minion(
    'Salty Looter', CardClass.ROGUE, MinionRace.PIRATE, 4, 4,
    cost=4, tier=3,
    _on_any_played=_salty_looter_on_any_played
)
SALTY_LOOTER_GOLDEN = Minion(
    'Salty Looter', CardClass.ROGUE, MinionRace.PIRATE, 8, 8,
    cost=4, tier=3, is_golden=True,
    _on_any_played=_salty_looter_on_any_played
)


def _southsea_strongarm_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Southsea Strongarm minion.
    Effect: Give a friendly Pirate +1/+1 (or +2/+2 if golden) for each Pirate you bought this turn.

    Note: the pirate is chosen RANDOMLY since we do not have targetting implemented.
    """
    minion = board.get_random_minion_on_board(race=MinionRace.PIRATE, ignore=[self])
    if minion is None:
        return

    n = len(board.get_minions_bought_this_turn(race=MinionRace.PIRATE, ignore=[self]))
    buff_amount = n * (2 if self.is_golden else 1)
    minion.add_buff(Buff(buff_amount, buff_amount, CardAbility.NONE))


SOUTHSEA_STRONGARM = Minion(
    'Southsea Strongarm', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 3,
    cost=5, tier=3, abilities=CardAbility.BATTLECRY,
    _on_this_played=_southsea_strongarm_on_this_played
)
SOUTHSEA_STRONGARM_GOLDEN = Minion(
    'Southsea Strongarm', CardClass.NEUTRAL, MinionRace.PIRATE, 8, 6,
    cost=5, tier=3, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_southsea_strongarm_on_this_played
)

# Neutral Pool
# NOTE: This effect requires reading a trace of the battle from the C++ simulator,
#       and then reflecting the changes in our game state representation.
#       (since we need to update the attack of the minion for future combat)
#
#       This means that the minion needs a way of hooking into the end of the combat phase,
#       so that it can read the output of the simulator and make the appropriate changes.
ARM_OF_THE_EMPIRE = Minion(
    'Arm of the Empire', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 5,
    cost=5, tier=3,
    #_on_end_combat_phase=???
)
ARM_OF_THE_EMPIRE_GOLDEN = Minion(
    'Arm of the Empire', CardClass.NEUTRAL, MinionRace.NEUTRAL, 8, 10,
    cost=5, tier=3, is_golden=True,
    #_on_end_combat_phase=???
)


def _khadgar_on_any_summoned(self: Minion, board: TavernGameBoard, summoned_minion: Minion) \
        -> None:
    """Handle the Khadgar minion effect.
    Effect (regular): Your cards that summon minions summon twice as many.
    Effect (golden):  Your cards that summon minions summon three times as many.
    """
    if summoned_minion is self:
        return
    times = 2 if self.is_golden else 1
    # Summon times copies of the summoned card.
    for _ in range(times):
        minion = summoned_minion.clone(keep_buffs=True)
        board.summon_minion(minion, call_events=False)


# NOTE: This requires changing the C++ simulator as well, since this effect applies
#       during the combat phase, as well as the recruitment phase.
KHADGAR = Minion(
    'Khadgar', CardClass.MAGE, MinionRace.NEUTRAL, 2, 2,
    cost=2, tier=3, rarity=CardRarity.LEGENDARY,
    _on_any_summoned=_khadgar_on_any_summoned
)
KHADGAR_GOLDEN = Minion(
    'Khadgar', CardClass.MAGE, MinionRace.NEUTRAL, 4, 4,
    cost=2, tier=3, rarity=CardRarity.LEGENDARY, is_golden=True,
    _on_any_summoned=_khadgar_on_any_summoned
)

# NOTE: This requires reading information from the C++ simulator.
WARDEN_OF_OLD = Minion(
    'Warden of Old', CardClass.NEUTRAL, MinionRace.NEUTRAL, 3, 3,
    cost=4, tier=3, abilities=CardAbility.DEATH_RATTLE
)
WARDEN_OF_OLD_GOLDEN = Minion(
    'Warden of Old', CardClass.NEUTRAL, MinionRace.NEUTRAL, 6, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

################################################################################
# Tier 4 cards
################################################################################
# Beast Pool

CAVE_HYDRA = Minion(
    'Cave Hydra', CardClass.HUNTER, MinionRace.BEAST, 2, 4,
    cost=3, tier=4
)
CAVE_HYDRA_GOLDEN = Minion(
    'Cave Hydra', CardClass.HUNTER, MinionRace.BEAST, 4, 8,
    cost=3, tier=4, is_golden=True
)

# Hyena summoned by Savannah Highmane
HYENA = Minion(
    'Hyena', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    cost=2, tier=1, purchasable=False
)
HYENA_GOLDEN = Minion(
    'Hyena', CardClass.HUNTER, MinionRace.BEAST, 4, 4,
    cost=2, tier=1, is_golden=True, purchasable=False
)

SAVANNAH_HIGHMANE = Minion(
    'Savannah Highmane', CardClass.HUNTER, MinionRace.BEAST, 6, 5,
    cost=6, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE
)
SAVANNAH_HIGHMANE_GOLDEN = Minion(
    'Savannah Highmane', CardClass.HUNTER, MinionRace.BEAST, 12, 10,
    cost=6, tier=4, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE
)


def _virmen_sensei_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Virmen Sensei minion.
    Effect: Give a friendly Beast +2/+2 (or +4/+4 if golden).

    Note: the beast is chosen RANDOMLY since we do not have targetting implemented.
    """
    minion = board.get_random_minion_on_board(race=MinionRace.BEAST, ignore=[self])
    if minion is None:
        return
    if self.is_golden:
        minion.add_buff(Buff(4, 4, CardAbility.NONE))
    else:
        minion.add_buff(Buff(2, 2, CardAbility.NONE))


VIRMEN_SENSEI = Minion(
    'Virmen Sensei', CardClass.DRUID, MinionRace.NONE, 4, 5,
    cost=5, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.BATTLECRY,
    _on_this_played=_virmen_sensei_on_this_played
)
VIRMEN_SENSEI_GOLDEN = Minion(
    'Virmen Sensei', CardClass.DRUID, MinionRace.NONE, 8, 10,
    cost=5, tier=4, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_virmen_sensei_on_this_played
)

# Demon Pool

BIGFERNAL = Minion(
    'Bigfernal', CardClass.NEUTRAL, MinionRace.DEMON, 4, 4,
    cost=5, tier=4
)
BIGFERNAL_GOLDEN = Minion(
    'Bigfernal', CardClass.NEUTRAL, MinionRace.DEMON, 8, 8,
    cost=5, tier=4, is_golden=True
)

RING_MATRON = Minion(
    'Ring Matron', CardClass.WARLOCK, MinionRace.DEMON, 6, 4,
    cost=6, tier=4, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)
RING_MATRON_GOLDEN = Minion(
    'Ring Matron', CardClass.WARLOCK, MinionRace.DEMON, 12, 8,
    cost=6, tier=4, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

SIEGEBREAKER = Minion(
    'Siegebreaker', CardClass.WARLOCK, MinionRace.DEMON, 5, 8,
    cost=7, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.TAUNT
)
SIEGEBREAKER_GOLDEN = Minion(
    'Siegebreaker', CardClass.WARLOCK, MinionRace.DEMON, 10, 16,
    cost=7, tier=4, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.TAUNT
)


# Dragon Pool
def _cobalt_scalebane_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the Cobalt Scalebane effect on the end of a turn.
    Effect: At the end of your turn, give another random friendly minion
    +3 (or +6 if golden) Attack.
    """
    minion = board.get_random_minion_on_board(ignore=[self])
    if minion is None:
        return
    if self.is_golden:
        minion.add_buff(Buff(6, 0, CardAbility.NONE))
    else:
        minion.add_buff(Buff(3, 0, CardAbility.NONE))


COBALT_SCALEBANE = Minion(
    'Cobalt Scalebane', CardClass.NEUTRAL, MinionRace.DRAGON, 5, 5,
    cost=5, tier=4,
    _on_end_turn=_cobalt_scalebane_on_end_turn
)
COBALT_SCALEBANE_GOLDEN = Minion(
    'Cobalt Scalebane', CardClass.NEUTRAL, MinionRace.DRAGON, 10, 10,
    cost=5, tier=4, is_golden=True,
    _on_end_turn=_cobalt_scalebane_on_end_turn
)

DRAKONID_ENFORCER = Minion(
    'Drakonid Enforcer', CardClass.NEUTRAL, MinionRace.DRAGON, 3, 6,
    cost=6, tier=4
)
DRAKONID_ENFORCER_GOLDEN = Minion(
    'Drakonid Enforcer', CardClass.NEUTRAL, MinionRace.DRAGON, 6, 12,
    cost=6, tier=4, is_golden=True
)

HERALD_OF_FLAME = Minion(
    'Herald of Flame', CardClass.WARLOCK, MinionRace.DRAGON, 5, 6,
    cost=5, tier=4
)
HERALD_OF_FLAME_GOLDEN = Minion(
    'Herald of Flame', CardClass.WARLOCK, MinionRace.DRAGON, 10, 12,
    cost=5, tier=4, is_golden=True
)


# Elemental Pool
def _majordomo_executus_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Majordomo Executus minion.
    Effect: At the end of your turn, give your left-most minion +1/+1 (or +2/+2 if golden).
            Repeat for each Elemental you played this turn.
    """
    # Get the left most minion
    minion = board.get_leftmost_minion_on_board()
    if minion is None:
        return
    # Apply buff once, and then additionally for each elemental played this turn.
    multiplier = len(board.get_minions_played_this_turn(race=MinionRace.ELEMENTAL)) + 1
    base_buff = 2 if self.is_golden else 1
    minion.add_buff(Buff(multiplier * base_buff, multiplier * base_buff, CardAbility.NONE))


MAJORDOMO_EXECUTUS = Minion(
    'Majordomo Executus', CardClass.NEUTRAL, MinionRace.DRAGON, 6, 3,
    cost=6, tier=4, rarity=CardRarity.LEGENDARY,
    _on_end_turn=_majordomo_executus_on_end_turn
)
MAJORDOMO_EXECUTUS_GOLDEN = Minion(
    'Majordomo Executus', CardClass.NEUTRAL, MinionRace.DRAGON, 12, 6,
    cost=6, tier=4, rarity=CardRarity.LEGENDARY, is_golden=True,
    _on_end_turn=_majordomo_executus_on_end_turn
)

WILDFIRE_ELEMENTAL = Minion(
    'Wildfire Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 7, 3,
    cost=6, tier=4
)
WILDFIRE_ELEMENTAL_GOLDEN = Minion(
    'Wildfire Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 14, 6,
    cost=6, tier=4, is_golden=True
)

# Mech Pool
ANNOY_O_MODULE = Minion(
    'Annoy-o-Module', CardClass.PALADIN, MinionRace.MECH, 2, 4,
    cost=4, tier=4, rarity=CardRarity.RARE,
    abilities=CardAbility.DIVINE_SHIELD | CardAbility.TAUNT
)
ANNOY_O_MODULE_GOLDEN = Minion(
    'Annoy-o-Module', CardClass.PALADIN, MinionRace.MECH, 4, 8,
    cost=4, tier=4, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.DIVINE_SHIELD | CardAbility.TAUNT
)

# Robosaur summoned by Mechano Egg
ROBOSAUR = Minion(
    'Robosaur', CardClass.PALADIN, MinionRace.MECH, 8, 8,
    cost=8, tier=1, purchasable=False
)
ROBOSAUR_GOLDEN = Minion(
    'Robosaur', CardClass.PALADIN, MinionRace.MECH, 16, 16,
    cost=8, tier=1, is_golden=True, purchasable=False
)

MECHANO_EGG = Minion(
    'Mechano-Egg', CardClass.PALADIN, MinionRace.MECH, 0, 5,
    cost=5, tier=4, abilities=CardAbility.DEATH_RATTLE
)
MECHANO_EGG_GOLDEN = Minion(
    'Mechano-Egg', CardClass.PALADIN, MinionRace.MECH, 0, 10,
    cost=5, tier=4, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# Guard Bot summoned by Security Rover
GUARD_BOT = Minion(
    'Guard Bot', CardClass.WARRIOR, MinionRace.MECH, 2, 3,
    cost=2, tier=1, purchasable=False, abilities=CardAbility.TAUNT
)
GUARD_BOT_GOLDEN = Minion(
    'Guard Bot', CardClass.WARRIOR, MinionRace.MECH, 4, 6,
    cost=2, tier=1, purchasable=False, is_golden=True, abilities=CardAbility.TAUNT
)

SECURITY_ROVER = Minion(
    'Security Rover', CardClass.WARLOCK, MinionRace.MECH, 2, 6,
    cost=6, tier=4
)
SECURITY_ROVER_GOLDEN = Minion(
    'Security Rover', CardClass.WARLOCK, MinionRace.MECH, 4, 12,
    cost=6, tier=4, is_golden=True
)

# Murloc Pool
# NOTE: Discover is a tricky thing to implement, so we will probably skip it!
#
# See https://www.reddit.com/r/hearthstone/comments/dzgrea/discover_mechanic/
# for details into how the discover mechanic is implemented (i.e. what pool of cards
# it selects from).
PRIMALFIN_LOOKOUT = Minion(
    'Primalfin Lookout', CardClass.NEUTRAL, MinionRace.MURLOC, 3, 2,
    cost=3, tier=4, abilities=CardAbility.BATTLECRY,
    # _on_this_played=???
)
PRIMALFIN_LOOKOUT_GOLDEN = Minion(
    'Primalfin Lookout', CardClass.NEUTRAL, MinionRace.MURLOC, 6, 4,
    cost=3, tier=4, is_golden=True, abilities=CardAbility.BATTLECRY,
    # _on_this_played=???
)


def _toxfin_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Toxfin minion.
    Effect: Give a friendly Murloc Poisonous.

    Note: the murloc is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Murloc
    minion = board.get_random_minion_on_board(race=MinionRace.MURLOC, ignore=[self])
    if minion is None:
        return
    minion.add_buff(Buff(0, 0, CardAbility.POISONOUS))


TOXFIN = Minion(
    'Toxfin', CardClass.NEUTRAL, MinionRace.MURLOC, 1, 2,
    cost=1, tier=4, abilities=CardAbility.BATTLECRY,
    _on_this_played=_toxfin_on_this_played
)
TOXFIN_GOLDEN = Minion(
    'Toxfin', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 4,
    cost=1, tier=4, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_toxfin_on_this_played
)


# Pirate Pool
def _goldgrubber_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Goldgrubber minion.
    Effect: At the end of your turn, gain +2/+2 (or +4/+4 if golden)
    for each friendly Golden minion.
    """
    multiplier = len(board.get_minions_on_board(is_golden=True))
    base_buff = 4 if self.is_golden else 2
    self.add_buff(Buff(multiplier * base_buff, multiplier * base_buff, CardAbility.NONE))


GOLDGRUBBER = Minion(
    'Goldgrubber', CardClass.NEUTRAL, MinionRace.PIRATE, 2, 2,
    cost=5, tier=4,
    _on_end_turn=_goldgrubber_on_end_turn
)
GOLDGRUBBER_GOLDEN = Minion(
    'Goldgrubber', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 4,
    cost=5, tier=4, is_golden=True,
    _on_end_turn=_goldgrubber_on_end_turn
)

RIPSNARL_CAPTAIN = Minion(
    'Ripsnarl Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 5,
    cost=4, tier=4
)
RIPSNARL_CAPTAIN_GOLDEN = Minion(
    'Ripsnarl Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 8, 10,
    cost=4, tier=4, is_golden=True
)

# Neutral Pool
BOLVAR_FIREBLOOD = Minion(
    'Bolvar, Fireblood', CardClass.PALADIN, MinionRace.NONE, 1, 7,
    cost=5, tier=4, rarity=CardRarity.LEGENDARY, abilities=CardAbility.DIVINE_SHIELD
)
BOLVAR_FIREBLOOD_GOLDEN = Minion(
    'Bolvar, Fireblood', CardClass.PALADIN, MinionRace.NONE, 2, 14,
    cost=5, tier=4, rarity=CardRarity.LEGENDARY, is_golden=True,
    abilities=CardAbility.DIVINE_SHIELD
)

CHAMPION_OF_YSHAARJ = Minion(
    'Champion of Y\'Shaarj', CardClass.NEUTRAL, MinionRace.NONE, 4, 4,
    cost=4, tier=4
)
CHAMPION_OF_YSHAARJ_GOLDEN = Minion(
    'Champion of Y\'Shaarj', CardClass.NEUTRAL, MinionRace.NONE, 8, 8,
    cost=4, tier=4, is_golden=True
)


def _defender_of_argus_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Defender of Argus minion.
    Effect: Give adjacent minions +1/+1 (or +2/+2 if golden) and Taunt.
    """
    if self.is_golden:
        buff = Buff(2, 2, CardAbility.TAUNT)
    else:
        buff = Buff(1, 1, CardAbility.TAUNT)

    index = board.get_index_of_minion_on_board(self)
    left, right = board.get_adjacent_minions(index)
    if left is not None:
        left.add_buff(buff)
    if right is not None:
        right.add_buff(buff)


DEFENDER_OF_ARGUS = Minion(
    'Defender of Argus', CardClass.NEUTRAL, MinionRace.NONE, 2, 3,
    cost=4, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.BATTLECRY,
    _on_this_played=_defender_of_argus_on_this_played
)
DEFENDER_OF_ARGUS_GOLDEN = Minion(
    'Defender of Argus', CardClass.NEUTRAL, MinionRace.NONE, 4, 6,
    cost=4, tier=4, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_defender_of_argus_on_this_played
)


def _managerie_jug_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Menagerie Jug effect.
    Effect: Give 3 random friendly minions of different minion types +2/+2 (or +4/+4 if golden).
    """
    minions_by_race = {}
    for minion in board.get_minions_on_board(ignore=[self]):
        if minion.race not in minions_by_race:
            minions_by_race[minion.race] = []
        minions_by_race[minion.race].append(minion)

    keys = random.sample(list(minions_by_race.keys()), k=min(3, len(minions_by_race)))
    for key in keys:
        minion = random.choice(minions_by_race[key])
        if self.is_golden:
            minion.add_buff(Buff(4, 4, CardAbility.NONE))
        else:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))


MENAGERIE_JUG = Minion(
    'Menagerie Jug', CardClass.NEUTRAL, MinionRace.NONE, 3, 3,
    cost=5, tier=4, abilities=CardAbility.BATTLECRY,
    _on_this_played=_managerie_jug_on_this_played
)
MENAGERIE_JUG_GOLDEN = Minion(
    'Menagerie Jug', CardClass.NEUTRAL, MinionRace.NONE, 6, 6,
    cost=5, tier=4, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_managerie_jug_on_this_played
)

QIRAJI_HARBINGER = Minion(
    'Qiraji Harbinger', CardClass.NEUTRAL, MinionRace.NONE, 5, 5,
    cost=6, tier=4
)
QIRAJI_HARBINGER_GOLDEN = Minion(
    'Qiraji Harbinger', CardClass.NEUTRAL, MinionRace.NONE, 10, 10,
    cost=6, tier=4, is_golden=True
)

################################################################################
# Tier 5 cards
################################################################################
# Beast Pool
# Ironhide Runt summoned by Ironhide Direhorn
IRONHIDE_RUNT = Minion(
    'Ironhide Runt', CardClass.DRUID, MinionRace.BEAST, 5, 5,
    cost=5, tier=1, purchasable=False
)

IRONHIDE_RUNT_GOLDEN = Minion(
    'Ironhide Runt', CardClass.DRUID, MinionRace.BEAST, 10, 10,
    cost=5, tier=1, is_golden=True, purchasable=False
)

IRONHIDE_DIREHORN = Minion(
    'Ironhide Direhorn', CardClass.DRUID, MinionRace.BEAST, 7, 7,
    cost=7, tier=5
)

IRONHIDE_DIREHORN_GOLDEN = Minion(
    'Ironhide Direhorn', CardClass.DRUID, MinionRace.BEAST, 14, 14,
    cost=7, tier=5, is_golden=True
)


def _mama_bear_on_any_summoned(self: Minion, board: TavernGameBoard,
                               summoned_minion: Minion) -> None:
    """Handle the Mama Bear effect
    Effect: Whenever you summon a Beast, give it +4/+4 (or +8/+8 if golden)."""
    if MinionRace.BEAST not in summoned_minion.race:
        return
    if self.is_golden:
        self.add_buff(Buff(8, 8, CardAbility.NONE))
    else:
        self.add_buff(Buff(4, 4, CardAbility.NONE))


MAMA_BEAR = Minion(
    'Mama Bear', CardClass.NEUTRAL, MinionRace.BEAST, 4, 4,
    cost=8, tier=5, rarity=CardRarity.EPIC,
    _on_any_summoned=_mama_bear_on_any_summoned
)

MAMA_BEAR_Golden = Minion(
    'Mama Bear', CardClass.NEUTRAL, MinionRace.BEAST, 8, 8,
    cost=8, tier=5, rarity=CardRarity.EPIC, is_golden=True,
    _on_any_summoned=_mama_bear_on_any_summoned
)


# Demon Pool
def _annihilian_battlemaster_on_any_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Annihilan Battlemaster minion.
    Effect: Gain +1 (+2 if Golden) Health for each damage your hero has taken.
    """
    to_gain = 40 - board.hero_health
    if self.is_golden:
        buff = Buff(2 * to_gain, 0, CardAbility.NONE)
    else:
        buff = Buff(to_gain, 0, CardAbility.NONE)

    self.add_buff(buff)


ANNIHILAN_BATTLEMASTER = Minion(
    'Annihilan Battlemaster', CardClass.NEUTRAL, MinionRace.DEMON, 3, 1,
    cost=8, tier=5, rarity=CardRarity.EPIC, abilities=CardAbility.BATTLECRY,
    _on_this_played=_annihilian_battlemaster_on_any_played
)

ANNIHILAN_BATTLEMASTER_GOLDEN = Minion(
    'Annihilan Battlemaster', CardClass.NEUTRAL, MinionRace.DEMON, 6, 2,
    cost=8, tier=5, rarity=CardRarity.EPIC, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_annihilian_battlemaster_on_any_played
)

MAL_GANIS = Minion(
    'Mal\'Ganis', CardClass.WARLOCK, MinionRace.DEMON, 9, 7,
    cost=9, tier=5, rarity=CardRarity.LEGENDARY,
)

MAL_GANIS_GOLDEN = Minion(
    'Mal\'Ganis', CardClass.WARLOCK, MinionRace.DEMON, 18, 14,
    cost=9, tier=5, rarity=CardRarity.LEGENDARY, is_golden=True
)

# Voidwalker summoned by voidlord
VOIDWALKER = Minion(
    'Voidwalker', CardClass.WARLOCK, MinionRace.DEMON, 1, 3,
    cost=1, tier=1, abilities=CardAbility.TAUNT, purchasable=False
)

VOIDWALKER_GOLDEN = Minion(
    'Voidwalker', CardClass.WARLOCK, MinionRace.DEMON, 2, 6, is_golden=True,
    cost=1, tier=1, abilities=CardAbility.TAUNT, purchasable=False
)

VOIDLORD = Minion(
    'Voidlord', CardClass.WARLOCK, MinionRace.DEMON, 3, 9,
    cost=9, tier=5, rarity=CardRarity.EPIC,
    abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

VOIDLORD_GOLDEN = Minion(
    'Voidlord', CardClass.WARLOCK, MinionRace.DEMON, 6, 18,
    cost=9, tier=5, rarity=CardRarity.EPIC, is_golden=True,
    abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

# Dragon Pool
MUROZOND = Minion(
    'Murozond', CardClass.NEUTRAL, MinionRace.DRAGON, 5, 5,
    cost=7, tier=5, abilities=CardAbility.BATTLECRY
)

MUROZOND_GOLDEN = Minion(
    'Murozond', CardClass.NEUTRAL, MinionRace.DRAGON, 10, 10,
    cost=7, tier=5, is_golden=True, abilities=CardAbility.BATTLECRY
)


def _razorgore_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Razorgore, the untamed minion.
    Effect: At the end of your turn, gain +1/+1 (or +2/+2 if golden)
    for each dragon you have.
    """
    multiplier = len(board.get_minions_on_board(race=MinionRace.DRAGON))
    base_buff = 2 if self.is_golden else 1
    self.add_buff(Buff(multiplier * base_buff, multiplier * base_buff, CardAbility.NONE))


RAZORGORE_THE_UNTAMED = Minion(
    'Razorgore, the Untamed', CardClass.NEUTRAL, MinionRace.DRAGON, 2, 4,
    cost=8, tier=5,
    _on_end_turn=_razorgore_on_end_turn
)

RAZORGORE_THE_UNTAMED_GOLDEN = Minion(
    'Razorgore, the Untamed', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 8,
    cost=8, tier=5, is_golden=True,
    _on_end_turn=_razorgore_on_end_turn
)

# Elemental Pool

def _nomi_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) -> None:
    """Handle the effect for the Nomi, Kitchen Nightmare minion.
    Effect: After you play an Elemental, Elementals in Bob's Tavern have +1/+1 (or +2/+2 if golden)
    for the rest of the game.
    """
    if MinionRace.ELEMENTAL not in played_minion.race:
        return
    for minion in board.get_minions_on_board(race=MinionRace.ELEMENTAL):
        if self.is_golden:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))
        else:
            minion.add_buff(Buff(1, 1, CardAbility.NONE))


NOMI_KITCHEN_NIGHTMARE = Minion(
    "Nomi, Kitchen Nightmare", CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 4,
    cost=7, tier=5, rarity=CardRarity.LEGENDARY,
    _on_any_played=_nomi_on_any_played
)

NOMI_KITCHEN_NIGHTMARE_GOLDEN = Minion(
    "Nomi, Kitchen Nightmare", CardClass.NEUTRAL, MinionRace.NEUTRAL, 8, 8,
    cost=7, tier=5, rarity=CardRarity.LEGENDARY, is_golden=True,
    _on_any_played=_nomi_on_any_played
)


def _tavern_tempest_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Sellemental minion.
    Effect: When you sell this, add a 2/2 Elemental to your hand (or 2 if golden).
    """
    n = 2 if self.is_golden else 1

    minions = board.get_minions(race=MinionRace.ELEMENTAL)
    for _ in range(n):
        board.add_minion_to_hand(random.choice(minions))


TAVERN_TEMPEST = Minion(
    "Tavern Tempest", CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=5, tier=5, abilities=CardAbility.BATTLECRY,
    _on_this_played=_tavern_tempest_on_this_played
)

TAVERN_TEMPEST_GOLD = Minion(
    "Tavern Tempest", CardClass.NEUTRAL, MinionRace.ELEMENTAL, 8, 8,
    cost=5, tier=5, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_tavern_tempest_on_this_played
)

# Mech Pool
JUNKBOT = Minion(
    "Junkbot", CardClass.NEUTRAL, MinionRace.MECH, 1, 5,
    cost=5, tier=5
)

JUNKBOT_GOLDEN = Minion(
    "Junkbot", CardClass.NEUTRAL, MinionRace.MECH, 2, 10,
    cost=5, tier=5, is_golden=True
)

SNEED_OLD_SHREDDER = Minion(
    "Sneed's Old Shredder", CardClass.NEUTRAL, MinionRace.MECH, 5, 7,
    cost=8, tier=5, rarity=CardRarity.LEGENDARY,
    abilities=CardAbility.DEATH_RATTLE
)

SNEED_OLD_SHREDDER_GOLDEN = Minion(
    "Sneed's Old Shredder", CardClass.NEUTRAL, MinionRace.MECH, 10, 14,
    cost=8, tier=5, rarity=CardRarity.LEGENDARY, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE
)


# Murloc pool
def _king_bargurgle_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the King Bagurgle minion.
    Effect: Give your other Murloc +2/+2 (or +4/+4 if golden).
    """
    additional = 4 if self.is_golden else 2
    minions = board.get_minions_on_board(race=MinionRace.MURLOC, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(additional, additional, CardAbility.NONE))


KING_BAGURGLE = Minion(
    "King Bargurgle", CardClass.NEUTRAL, MinionRace.MURLOC, 6, 3,
    cost=6, tier=5, rarity=CardRarity.LEGENDARY,
    abilities=CardAbility.BATTLECRY | CardAbility.DEATH_RATTLE,
    _on_this_played=_king_bargurgle_on_this_played
)

KING_BAGURGLE_GOLDEN = Minion(
    "King Bargurgle", CardClass.NEUTRAL, MinionRace.MURLOC, 12, 6,
    cost=6, tier=5,  is_golden=True, rarity=CardRarity.LEGENDARY,
    abilities=CardAbility.BATTLECRY | CardAbility.DEATH_RATTLE,
    _on_this_played=_king_bargurgle_on_this_played
)

# Pirate Pool
CAPN_HOGGARR = Minion(
    'Cap\'n Hoggarr', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=6, tier=5
)

CAPN_HOGGARR_GOLDEN = Minion(
    'Cap\'n Hoggarr', CardClass.NEUTRAL, MinionRace.PIRATE, 12, 12,
    cost=6, tier=5, is_golden=True
)

NAT_PAGLE = Minion(
    'Nat Pagle, Extreme Angler', CardClass.NEUTRAL, MinionRace.PIRATE, 8, 5,
    cost=7, tier=5
)

NAT_PAGLE_GOLDEN = Minion(
    'Nat Pagle, Extreme Angler', CardClass.NEUTRAL, MinionRace.PIRATE, 16, 10,
    cost=7, tier=5, is_golden=True
)

SEABREAKER_GOLIATH = Minion(
    'Seabreaker Goliath', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 7,
    cost=7, tier=5, abilities=CardAbility.WINDFURY
)

SEABREAKER_GOLIATH_GOLDEN = Minion(
    'Seabreaker Goliath', CardClass.NEUTRAL, MinionRace.PIRATE, 12, 14,
    cost=7, tier=5, is_golden=True, abilities=CardAbility.MEGA_WINDFURY
)

# Neutral
BARON_RIVENDARE = Minion(
    'Baron Rivendare', CardClass.NEUTRAL, MinionRace.NEUTRAL, 1, 7,
    cost=4, tier=5, rarity=CardRarity.LEGENDARY
)

BARON_RIVENDARE_GOLDEN = Minion(
    'Baron Rivendare', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 14,
    cost=4, tier=5, is_golden=True, rarity=CardRarity.LEGENDARY
)

BRANN_BRONZEBEARD = Minion(
    'Brann Bronzebeard', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 4,
    cost=3, tier=5, rarity=CardRarity.LEGENDARY
)

BRANN_BRONZEBEARD_GOLDEN = Minion(
    'Brann Bronzebeard', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 8,
    cost=3, tier=5, rarity=CardRarity.LEGENDARY, is_golden=True
)

DEADLY_SPORE = Minion(
    'Deadly Spore', CardClass.NEUTRAL, MinionRace.NEUTRAL, 1, 1,
    cost=4, tier=5, abilities=CardAbility.POISONOUS
)

DEADLY_SPORE_GOLDEN = Minion(
    'Deadly Spore', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 2,
    cost=4, tier=5, is_golden=True, abilities=CardAbility.POISONOUS
)

FACELESS_TAVERNGOER = Minion(
    'Faceless Taverngoer', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 4,
    cost=4, tier=5, abilities=CardAbility.BATTLECRY
)

FACELESS_TAVERNGOER_GOLDEN = Minion(
    'Faceless Taverngoer', CardClass.NEUTRAL, MinionRace.NEUTRAL, 8, 8,
    cost=4, tier=5, is_golden=True, abilities=CardAbility.BATTLECRY
)


def _lightfang_enforcer_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Lightfang Enforcer minion.
    Effect: At the end of your turn, give a friendly minion of each minion type a +2/+2 (+4/+4)/
    """
    minions_by_race = {}
    for minion in board.get_minions_on_board(ignore=[self]):
        if minion.race not in minions_by_race:
            minions_by_race[minion.race] = []
        minions_by_race[minion.race].append(minion)

    for minion_race in minions_by_race:
        minion = random.choice(minions_by_race[minion_race])
        if self.is_golden:
            minion.add_buff(Buff(4, 4, CardAbility.NONE))
        else:
            minion.add_buff(Buff(2, 2, CardAbility.NONE))


LIGHTFANG_ENFORCER = Minion(
    'Lightfang Enforcer', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 2,
    cost=6, tier=5,
    _on_end_turn=_lightfang_enforcer_on_end_turn
)

LIGHTFANG_ENFORCER_GOLDEN = Minion(
    'Lightfang Enforcer', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 4,
    cost=6, tier=5, is_golden=True,
    _on_end_turn=_lightfang_enforcer_on_end_turn
)


def _mythrax_on_end_turn(self: Minion, board: TavernGameBoard) -> None:
    """Handle the effect for the Mythrax, the unraveler minion.
    Effect: At the end of your turn, gain +1/+2 (+2/+4) for each minion type you control.
    """
    minions_by_race = {}
    for minion in board.get_minions_on_board(ignore=[self]):
        if minion.race not in minions_by_race:
            minions_by_race[minion.race] = []
        minions_by_race[minion.race].append(minion)

    multiplier = len(minions_by_race)
    base_buff = 2 if self.is_golden else 1
    self.add_buff(Buff(multiplier * base_buff, multiplier * base_buff * 2, CardAbility.NONE))


MYTHRAX_THE_UNRAVELER = Minion(
    'Mythrax the Unraveler', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 4,
    cost=5, tier=5,
    _on_end_turn=_mythrax_on_end_turn
)

MYTHRAX_THE_UNRAVELER_GOLDEN = Minion(
    'Mythrax the Unraveler', CardClass.NEUTRAL, MinionRace.NEUTRAL, 8, 8,
    cost=5, tier=5, is_golden=True,
    _on_end_turn=_mythrax_on_end_turn
)


def _strongshell_scavenger_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Strongshell Scavenger minion.
    Effect: Give your Taunt minions +2/+2 (+4/+4 if golden)
    """
    additional = 4 if self.is_golden else 2
    minions = board.get_minions_on_board(abilities=CardAbility.TAUNT)
    for minion in minions:
        minion.add_buff(Buff(additional, additional, CardAbility.NONE))


STRONGSHELL_SCAVENGER = Minion(
    'Strongshell Scavenger', CardClass.NEUTRAL, MinionRace.NEUTRAL, 2, 3,
    cost=4, tier=5, rarity=CardRarity.RARE, abilities=CardAbility.BATTLECRY,
    _on_this_played=_strongshell_scavenger_on_this_played
)

STRONGSHELL_SCAVENGER_GOLDEN = Minion(
    'Strongshell Scavenger', CardClass.NEUTRAL, MinionRace.NEUTRAL, 4, 6,
    cost=4, tier=5, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=_strongshell_scavenger_on_this_played
)

################################################################################
# Tier 6 cards
################################################################################
# Beast Pool
GHASTCOILER = Minion(
    'Ghastcoiler', CardClass.PRIEST, MinionRace.BEAST, 7, 7,
    cost=6, tier=6, abilities=CardAbility.DEATH_RATTLE
)

GHASTCOILER_GOLDEN = Minion(
    'Ghastcoiler', CardClass.PRIEST, MinionRace.BEAST, 14, 14,
    cost=6, tier=6, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

GOLDRINN = Minion(
    'Goldrinn, the Great Wolf', CardClass.NEUTRAL, MinionRace.BEAST, 4, 4,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, abilities=CardAbility.DEATH_RATTLE
)

GOLDRINN_GOLDEN = Minion(
    'Goldrinn, the Great Wolf', CardClass.NEUTRAL, MinionRace.BEAST, 8, 8,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

MAEXXNA = Minion(
    'Maexxna', CardClass.NEUTRAL, MinionRace.BEAST, 2, 8,
    cost=6, rarity=CardRarity.LEGENDARY, tier=6, abilities=CardAbility.POISONOUS
)

MAEXXNA_GOLD = Minion(
    'Maexxna', CardClass.NEUTRAL, MinionRace.BEAST, 4, 16,
    cost=6, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True, abilities=CardAbility.POISONOUS
)

# Demon Pool
IMP_MAMA = Minion(
    'Imp Mama', CardClass.NEUTRAL, MinionRace.DEMON, 6, 10,
    cost=8, tier=6
)

IMP_MAMA_GOLDEN = Minion(
    'Imp Mama', CardClass.NEUTRAL, MinionRace.DEMON, 12, 20,
    cost=8, tier=6, is_golden=True
)


# Dragon Pool
def _kalecgos_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the Kalecgos, Arcane Aspect effect.
    Effect: After you play a minion with Battlecry, give your Dragons +1/+1.
    """
    if CardAbility.BATTLECRY not in played_minion.abilities:
        return
    additional = 2 if self.is_golden else 1
    minions = board.get_minions_on_board(race=MinionRace.DRAGON, ignore=[self])
    for minion in minions:
        minion.add_buff(Buff(additional, additional, CardAbility.NONE))


KALECGOS = Minion(
    'Kalecgos, Arcane Aspect', CardClass.NEUTRAL, MinionRace.DRAGON, 4, 12,
    cost=8, tier=6,
    _on_any_played=_kalecgos_on_any_played
)

KALECGOS_GOLDEN = Minion(
    'Kalecgos, Arcane Aspect', CardClass.NEUTRAL, MinionRace.DRAGON, 8, 24,
    cost=8, tier=6, is_golden=True,
    _on_any_played=_kalecgos_on_any_played
)

NADINA_THE_RED = Minion(
    'Nadina the Red', CardClass.NEUTRAL, MinionRace.DRAGON, 7, 4,
    cost=6, tier=6, abilities=CardAbility.DEATH_RATTLE
)

NADINA_THE_RED_GOLDEN = Minion(
    'Nadina the Red', CardClass.NEUTRAL, MinionRace.DRAGON, 14, 8,
    cost=6, tier=6, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# Elemental Pool
GENTLE_DJINNI = Minion(
    'Gentle Djinni', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 5,
    cost=6, tier=6, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

GENTLE_DJINNI_GOLDEN = Minion(
    'Gentle Djinni', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 8, 10,
    cost=6, tier=6, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)


def _lieutenant_garr_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the effect for the Lieutenant Garr minion.
    Effect: After you play an Elemental, gain +1 Health for each Elemental you have.
    """
    if played_minion is self or MinionRace.ELEMENTAL not in played_minion.race:
        return
    multiplier = len(board.get_minions_on_board(race=MinionRace.ELEMENTAL))
    base_buff = 2 if self.is_golden else 1
    self.add_buff(Buff(multiplier * base_buff, 0, CardAbility.NONE))


LIEUTENANT_GARR = Minion(
    'Lieutenant Garr', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 8, 1,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, abilities=CardAbility.TAUNT,
    _on_any_played=_lieutenant_garr_on_any_played
)

LIEUTENANT_GARR_GOLDEN = Minion(
    'Lieutenant Garr', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 16, 2,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True, abilities=CardAbility.TAUNT,
    _on_any_played=_lieutenant_garr_on_any_played
)


def _lil_rag_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) \
        -> None:
    """Handle the effect for the Lil' Rag minion.
    Effect: After you play an Elemental, give a friendly minion stats equal
    to the Elemental's Tavern Tier.
    """
    if played_minion is self or MinionRace.ELEMENTAL not in played_minion.race:
        return
    times = 2 if self.is_golden else 1
    for _ in range(times):
        minion = board.get_random_minion_on_board(ignore=[self, played_minion])
        minion.add_buff(Buff(played_minion.tier, played_minion.tier, CardAbility.NONE))


LIL_RAG = Minion(
    'Lil\' Rag', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 6, 6,
    cost=6, rarity=CardRarity.LEGENDARY, tier=6,
    _on_any_played=_lil_rag_on_any_played
)

LIL_RAG_GOLDEN = Minion(
    'Lil\' Rag', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 12, 12,
    cost=6, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True,
    _on_any_played=_lil_rag_on_any_played
)

# Mech Pool
FOE_REAPER_4000 = Minion(
    'Foe Reaper 4000', CardClass.NEUTRAL, MinionRace.MECH, 6, 9,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6
)

FOE_REAPER_4000_GOLDEN = Minion(
    'Foe Reaper 4000', CardClass.NEUTRAL, MinionRace.MECH, 12, 18,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True
)

KANGORS_APPRENTICE = Minion(
    'Kangor\'s Apprentice', CardClass.NEUTRAL, MinionRace.MECH, 4, 8,
    cost=9, rarity=CardRarity.EPIC, tier=6, abilities=CardAbility.DEATH_RATTLE
)

KANGORS_APPRENTICE_GOLDEN = Minion(
    'Kangor\'s Apprentice', CardClass.NEUTRAL, MinionRace.MECH, 8, 16,
    cost=9, rarity=CardRarity.EPIC, tier=6, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# Pirate Pool
DREAD_ADMIRAL_ELIZA = Minion(
    'Dread Admiral Eliza', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 7,
    cost=6, tier=6
)

DREAD_ADMIRAL_ELIZA_GOLDEN = Minion(
    'Dread Admiral Eliza', CardClass.NEUTRAL, MinionRace.PIRATE, 12, 14,
    cost=6, tier=6, is_golden=True
)

THE_TIDE_RAZOR = Minion(
    'The Tide Razor', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 4,
    cost=7, tier=6, abilities=CardAbility.DEATH_RATTLE
)

THE_TIDE_RAZOR_GOLDEN = Minion(
    'The Tide Razor', CardClass.NEUTRAL, MinionRace.PIRATE, 12, 8,
    cost=7, tier=6, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# Neutral Pool
AMALGADON = Minion(
    'Amalgadon', CardClass.NEUTRAL, MinionRace.ALL, 6, 6,
    cost=8, tier=6, abilities=CardAbility.BATTLECRY
)

AMALGADON_GOLDEN = Minion(
    'Amalgadon', CardClass.NEUTRAL, MinionRace.ALL, 12, 12,
    cost=8, tier=6, is_golden=True, abilities=CardAbility.BATTLECRY
)

ZAPP_SLYWICK = Minion(
    'Zapp Slywick', CardClass.NEUTRAL, MinionRace.NEUTRAL, 7, 10,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, abilities=CardAbility.WINDFURY
)

ZAPP_SLYWICK_GOLDEN = Minion(
    'Zapp Slywick', CardClass.NEUTRAL, MinionRace.NEUTRAL, 14, 20,
    cost=8, rarity=CardRarity.LEGENDARY, tier=6, is_golden=True
)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    parser = argparse.ArgumentParser(description='Command-line tool to view all minions.')
    parser.add_argument('task', help='The task to execute', choices={'scan', 'verify'}, nargs='?')
    parser.add_argument('--card-data', dest='card_data_path', type=Path, default=None,
                        help='HearthstoneJSON card data.')
    args = parser.parse_args()
    if args.task == 'scan':
        _scan_minion_list()
    elif args.task == 'verify':
        if args.card_data_path is None:
            raise ValueError(
                'The card_data_path argument (--card-data) is required '
                'for the \'verify\' task.'
            )
        _verify_minion_list(args.card_data_path)
    elif args.task is not None:
        raise ValueError(f'\'{args.task}\' is an invalid task!')
