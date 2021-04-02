"""Implementation of various minion cards.

These minions are implemented for Hearthstone Patch 20.0.
Data Source: https://hearthstone.fandom.com/wiki/Battlegrounds#Minions_by_tier

NOTE: This is a collection of all minions in the Battlegrounds pool as of Patch 20.0.
      However, not all of these minions are implemented. They are merely defined here
      in case that they should be implemented in the future.

      Refer to the minion_list.txt file for a full list of all minions with implementations
      in the Python recruitment phase simulator, and the C++ combat phase simulator.
"""
from __future__ import annotations
import random
import logging
from typing import List, Set, Dict, Optional, Union

from hsbg.utils import filter_minions
from hsbg.models import CardClass, CardRarity, CardAbility, MinionRace, Buff, Minion


def get_all_minions(gold_suffix: str = '_golden', whitelist: Optional[Set[str]] = None) \
        -> Dict[str, Minion]:
    """Return a dict mapping the name of each minion defined in the hsbg.minions module to
    its Minion object instance.

    Each key in the returned dict is the name of a minion (with an additional suffix if the
    minion is golden, specified by the gold_suffix argument).

    Args:
        gold_suffix: The suffix to add to keys representing minions that are golden.
        whitelist: A set containing the names of minions to include.
                   If None, then all minions are included.
    """
    all_minions = {}
    globals_copy = globals().copy()
    for obj in globals_copy.values():
        if not isinstance(obj, Minion) or (whitelist is not None and obj.name not in whitelist):
            continue
        key = obj.name + (gold_suffix if obj.is_golden else '')

        # Warn the user if duplicate minions were found!
        if key in all_minions:
            logging.warn(f'Found duplicate minion (\'{key}\')')

        all_minions[key] = obj
    return all_minions


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
    #   - _all_minions: A dict containing all the minions mapped by name.
    #   - _pool: A list of minions representing the current pool.
    #   - _gold_suffix: The suffix used to denote gold copies of minions.
    _all_minions: Dict[str, Minion]
    _pool: List[Minion]
    _gold_suffix: str

    def __init__(self, gold_suffix: str = '_golden') -> None:
        self._all_minions = {}
        self._pool = []
        self._gold_suffix = gold_suffix

        minions = get_all_minions(gold_suffix=gold_suffix)
        # Build the pool
        for key, minion in minions.items():
            self._all_minions[key] = minion

            # Don't include unpurchasable minions or golden copies in the pool.
            if not minion.purchasable or minion.is_golden:
                continue

            copies = TIER_NUM_COPIES[minion.tier]
            for _ in range(copies):
                self._pool.append(minion)

    def find_all(self, limit: Optional[int] = None, **kwargs: dict) -> List[Minion]:
        """Find all the minions matching the given keyword arguments.
        Each keyword argument should be an attribute of the Minion class.

        Note: the returned list contains COPIES of the minions in the pool.
        """
        return filter_minions(self._all_minions.values(), clone=True, limit=limit, **kwargs)

    def find(self, **kwargs: dict) -> Optional[Minion]:
        """Find the first minion matching the given keyword arguments.
        Each keyword argument should be an attribute of the Minion class.
        """
        minions = self.find_all(limit=1, **kwargs)
        return None if len(minions) == 0 else minions[0]

    def get_random(self, n: int = 1, max_tier: Optional[int] = None, remove: bool = True,
                   predicate: Optional[callable] = None) -> List[Minion]:
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
        def _predicate(x: Minion) -> bool:
            if max_tier is not None and x.tier > max_tier:
                return False
            if predicate is not None:
                return predicate(x)
            return True

        pool_subset = list(filter(_predicate, self._pool))
        minions = random.sample(pool_subset, k=n)
        if remove:
            # Remove each minion from the pool
            for minion in minions:
                self._pool.remove(minion)
        # Make a clone of each minion
        return [minion.clone() for minion in minions]

    def get_golden(self, name: str) -> Minion:
        """Return a golden copy of the minion with the given name.
        Raise a ValueError if there is no minion with that name, or if it has no golden copy.
        """
        if name not in self._all_minions:
            raise ValueError(f'Could not find minion with name \'{name}\' in the pool.')

        golden_copy_name = name + self._gold_suffix
        if golden_copy_name not in self._all_minions:
            raise ValueError(f'The minion with name \'{name}\' has no golden copy.')

        return self._all_minions[golden_copy_name].clone()

    def insert(self, values: Union[Minion, List[Minion]]) -> None:
        """Insert the given minions into the pool."""
        if isinstance(values, Minion):
            values = [values]
        for minion in values:
            self._pool.append(minion.clone())

    @property
    def size(self) -> int:
        """Return the number of minions in the pool (including copies)."""
        return len(self._pool)


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
    abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, board: board.summon_minion(board.pool.find(name='Tabbycat', is_golden=False))
)
ALLEYCAT_GOLDEN = Minion(
    'Alleycat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    is_golden=True, abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, board: board.summon_minion(board.pool.find(name='Tabbycat', is_golden=True))
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
# TODO: Deathrattle (Give this minion's attack to a random friendly minion)
FIENDISH_SERVANT = Minion(
    'Fiendish Servant', CardClass.WARLOCK, MinionRace.DEMON, 2, 2,
    abilities=CardAbility.DEATH_RATTLE
)
FIENDISH_SERVANT_GOLDEN = Minion(
    'Fiendish Servant', CardClass.WARLOCK, MinionRace.DEMON, 4, 2,
    is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

VULGAR_HOMUNCULUS = Minion(
    'Vulgar Homunculus', CardClass.WARLOCK, MinionRace.DEMON, 2, 4,
    cost=2, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=lambda self, board: board.attack_hero(2)
)
VULGAR_HOMUNCULUS_GOLDEN = Minion(
    'Vulgar Homunculus', CardClass.WARLOCK, MinionRace.DEMON, 4, 8,
    cost=2, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=lambda self, board: board.attack_hero(2)
)

def _wrath_weaver_on_any_played(self: Minion, board: TavernGameBoard, played_minion: Minion) -> None:
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

# TODO: Start of combat (Deal 1 damage per friendly Dragon to one random enemy minion).
RED_WHELP = Minion(
    'Red Whelp', CardClass.NEUTRAL, MinionRace.DRAGON, 1, 2,
    abilities=CardAbility.START_OF_COMBAT
)
RED_WHELP_GOLDEN = Minion(
    'Red Whelp', CardClass.NEUTRAL, MinionRace.DRAGON, 1, 2,
    is_golden=True, abilities=CardAbility.START_OF_COMBAT
)

# Elemental Pool
REFRESHING_ANOMALY = Minion(
    'Refreshing Anomaly', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 1, 3,
    abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda self, board: board.set_refresh_cost(0, times=1)
)
REFRESHING_ANOMALY_GOLDEN = Minion(
    'Refreshing Anomaly', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 6,
    is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda self, board: board.set_refresh_cost(0, times=2)
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
    cost=3, abilities=CardAbility.GENERATE,
    _on_this_sold=_sellemental_on_this_sold
)
SELLEMENTAL_GOLDEN = Minion(
    'Sellemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, abilities=CardAbility.GENERATE, is_golden=True,
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
    abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, board: board.summon_minion(board.pool.find(name='Murloc Scout', is_golden=False))
)
MURLOC_TIDEHUNTER_GOLDEN = Minion(
    'Murloc Tidehunter', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 2,
    cost=2, is_golden=True, abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, board: board.summon_minion(board.pool.find(name='Murloc Scout', is_golden=True))
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

# TODO: Deathrattle (Summon a 1/1 Pirate. It attacks immediately.)
SCALLYWAG = Minion(
    'Scallywag', CardClass.NEUTRAL, MinionRace.PIRATE, 2, 1,
    abilities=CardAbility.DEATH_RATTLE
)
# TODO: Deathrattle (Summon a 2/2 Pirate. It attacks immediately.)
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

# TODO: Deathrattle (Summon a 3/2 Big Bad Wolf.)
KINDLY_GRANDMOTHER = Minion(
    'Kindly Grandmother', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    cost=2, tier=2, abilities=CardAbility.DEATH_RATTLE
)
# TODO: Deathrattle (Summon a 6/4 Big Bad Wolf.)
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
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 2, 3,
    cost=2, tier=2, rarity=CardRarity.RARE,
    _on_any_summoned=_pack_leader_on_any_summoned
)
PACK_LEADER_GOLDEN = Minion(
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 4, 6,
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

# TODO: Deathrattle (Summon a 1/1 imp)
IMPRISONER = Minion(
    'Imprisoner', CardClass.NEUTRAL, MinionRace.DEMON, 3, 3,
    cost=3, tier=2, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Deathrattle (Summon a 2/2 imp)
IMPRISONER_GOLDEN = Minion(
    'Imprisoner', CardClass.NEUTRAL, MinionRace.DEMON, 6, 6,
    cost=3, tier=2, is_golden=True,
    abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE | CardAbility.SUMMON
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
# TODO: Implement effect: Whenever this attacks, DOUBLE its attack.
#       This requires implementing the effect in the C++ simulator!
GLYPH_GUARDIAN = Minion(
    'Glyph Guardian', CardClass.MAGE, MinionRace.DRAGON, 2, 4,
    cost=3, tier=2
)
# TODO: Implement effect: Whenever this attacks, TRIPLE its attack.
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

# TODO: Implement effect: Whenever a friendly Dragon kills an enemy, gain +2/+2.
WAXRIDER_TOGWAGGLE = Minion(
    'Waxrider Togwaggle', CardClass.NEUTRAL, MinionRace.NONE, 1, 3,
    cost=3, tier=2
)
# TODO: Implement effect: Whenever a friendly Dragon kills an enemy, gain +4/+4.
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

# TODO: Implement deathrattle (Summon a 2/1 Damaged Golem).
HARVEST_GOLEM = Minion(
    'Harvest Golem', CardClass.NEUTRAL, MinionRace.MECH, 2, 3,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Summon a 4/2 Damaged Golem).
HARVEST_GOLEM_GOLDEN = Minion(
    'Harvest Golem', CardClass.NEUTRAL, MinionRace.MECH, 4, 6,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# TODO: Implement deathrattle (Deal 4 damage to a random enemy minion).
KABOOM_BOT = Minion(
    'Kaboom Bot', CardClass.NEUTRAL, MinionRace.MECH, 2, 2,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Deal 4 damage to a random enemy minion twice).
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
    cost=4, tier=2, rarity=CardRarity.LEGENDARY, abilities=CardAbility.CHARGE
)
OLD_MURK_EYE_GOLDEN = Minion(
    'Old Murk-Eye', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 8,
    cost=4, tier=2, rarity=CardRarity.LEGENDARY, is_golden=True, abilities=CardAbility.CHARGE
)

# Pirate Pool
FREEDEALING_GAMBLER = Minion(
    'Freedealing Gambler', CardClass.NEUTRAL, MinionRace.PIRATE, 3, 3,
    cost=3, tier=2,
    # Effect: This minion sells for 3 golds.
    _on_this_sold=lambda self, board: board.give_gold(abs(3 - board._minion_sell_price))
)
FREEDEALING_GAMBLER_GOLDEN = Minion(
    'Freedealing Gambler', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=3, tier=2, is_golden=True,
    # Effect: This minion sells for 6 golds.
    _on_this_sold=lambda self, board: board.give_gold(abs(6 - board._minion_sell_price))
)

# TODO: Implement effect: Your other Pirates have +1/+1.
SOUTHSEA_CAPTAIN = Minion(
    'Southsea Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 3, 3,
    cost=3, tier=2, rarity=CardRarity.EPIC
)
# TODO: Implement effect: Your other Pirates have +2/+2.
SOUTHSEA_CAPTAIN_GOLDEN = Minion(
    'Southsea Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=3, tier=2, rarity=CardRarity.EPIC, is_golden=True
)

# TODO: Implement effect: After this minion survives being attacked, attack immediately.
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

# TODO: Implement deathrattle (Give your minions +1/+1).
SPAWN_OF_NZOTH = Minion(
    'Spawn of N\'Zoth', CardClass.NEUTRAL, MinionRace.NONE, 2, 2,
    cost=3, tier=2, abilities=CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Give your minions +2/+2).
SPAWN_OF_NZOTH_GOLDEN = Minion(
    'Spawn of N\'Zoth', CardClass.NEUTRAL, MinionRace.NONE, 4, 4,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# TODO: Implement deathrattle (Give a random friendly minion Divine Shield).
SELFLESS_HERO = Minion(
    'Selfless Hero', CardClass.PALADIN, MinionRace.NONE, 2, 1,
    cost=1, tier=2, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Give 2 random friendly minions Divine Shield).
SELFLESS_HERO_GOLDEN = Minion(
    'Selfless Hero', CardClass.PALADIN, MinionRace.NONE, 4, 2,
    cost=1, tier=2, rarity=CardRarity.RARE, is_golden=True, abilities=CardAbility.DEATH_RATTLE
)

# TODO: Implement effect: Whenever this is attacked, give adjacent minions +1/+1.
TORMENETED_RITUALIST = Minion(
    'Tormented Ritualist', CardClass.NEUTRAL, MinionRace.NONE, 2, 3,
    cost=3, tier=2, abilities=CardAbility.TAUNT
)
# TODO: Implement effect: Whenever this is attacked, give adjacent minions +2/+2.
TORMENETED_RITUALIST_GOLDEN = Minion(
    'Tormented Ritualist', CardClass.NEUTRAL, MinionRace.NONE, 4, 6,
    cost=3, tier=2, is_golden=True, abilities=CardAbility.TAUNT
)

# TODO: Implement deathrattle (Deal 1 damage to all minions).
UNSTABLE_GHOUL = Minion(
    'Unstable Ghoul', CardClass.NEUTRAL, MinionRace.NONE, 1, 3,
    cost=2, tier=2, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Deal 1 damage to all minions TWICE).
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

# TODO: Implement deathrattle (Summon two 1/1 Spiders).
INFESTED_WOLF = Minion(
    'Infested Wolf', CardClass.HUNTER, MinionRace.BEAST, 3, 3,
    cost=4, tier=3, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Implement deathrattle (Summon two 2/2 Spiders).
INFESTED_WOLF_GOLDEN = Minion(
    'Infested Wolf', CardClass.HUNTER, MinionRace.BEAST, 6, 6,
    cost=4, tier=3, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)

# TODO: Implement effect: After this attacks, trigger a random friendly minion's Deathrattle.
MONSTROUS_MACAW = Minion(
    'Monstrous Macaw', CardClass.NEUTRAL, MinionRace.BEAST, 4, 3,
    cost=3, tier=3
)
# TODO: Implement effect: After this attacks, trigger a random friendly minion's Deathrattle TWICE.
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

# TODO: Implement deathrattle (Summon a number of 1/1 Rats equal to this minion's Attack).
RAT_PACK = Minion(
    'Rat Pack', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    cost=3, tier=3, rarity=CardRarity.EPIC,
    abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Implement deathrattle (Summon a number of 2/2 Rats equal to this minion's Attack).
RAT_PACK_GOLDEN = Minion(
    'Rat Pack', CardClass.HUNTER, MinionRace.BEAST, 4, 4,
    cost=3, tier=3, rarity=CardRarity.EPIC, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)

# Demon Pool
# TODO: Implement effect: Whenever this minion takes damage, summon a 1/1 Imp.
IMP_GANG_BOSS = Minion(
    'Imp Gang Boss', CardClass.WARLOCK, MinionRace.DEMON, 2, 4,
    cost=3, tier=3, abilities=CardAbility.SUMMON
)
# TODO: Implement effect: Whenever this minion takes damage, summon a 2/2 Imp.
IMP_GANG_BOSS_GOLDEN = Minion(
    'Imp Gang Boss', CardClass.WARLOCK, MinionRace.DEMON, 4, 8,
    cost=3, tier=3, is_golden=True, abilities=CardAbility.SUMMON
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

# TODO: Implement effect: After a friendly Demon dies, deal 3 damage to a random enemy minion.
SOUL_JUGGLER = Minion(
    'Soul Juggler', CardClass.WARLOCK, MinionRace.NONE, 3, 3,
    cost=3, tier=3
)
# TODO: Implement effect: After a friendly Demon dies, deal 3 damage to a random enemy minion TWICE.
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
# TODO: Implement effect: Whenever you summon a Mech during combat, gain +1 Attack and Divine Shield.
DEFLECT_O_BOT = Minion(
    'Deflect-o-Bot', CardClass.NEUTRAL, MinionRace.MECH, 3, 2,
    cost=4, tier=3, abilities=CardAbility.DIVINE_SHIELD
)
# TODO: Implement effect: Whenever you summon a Mech during combat, gain +2 Attack and Divine Shield.
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

# TODO: Implement deathrattle (Summon a random 2-cost minion).
PILOTED_SHREDDER = Minion(
    'Piloted Shredder', CardClass.NEUTRAL, MinionRace.MECH, 4, 3,
    cost=4, tier=3, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Implement deathrattle (Summon two random 2-cost minions).
PILOTED_SHREDDER_GOLDEN = Minion(
    'Piloted Shredder', CardClass.NEUTRAL, MinionRace.MECH, 8, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
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
    cost=4, tier=3, abilities=CardAbility.MAGNETIC | CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
REPLICATING_MENACE_GOLDEN = Minion(
    'Replicating Menace', CardClass.NEUTRAL, MinionRace.MECH, 6, 2,
    cost=4, tier=3, is_golden=True,
    abilities=CardAbility.MAGNETIC | CardAbility.DEATH_RATTLE | CardAbility.SUMMON
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
    if MinionRace.PIRATE not in played_minion.race:
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
    minion = board.get_random_minion_on_board(ignore=[self])
    if minion is None:
        return

    n = len(board.get_bought_minions_this_turn(race=MinionRace.PIRATE))
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
# TODO: Implement effect: Whenever a friendly TAUNT minion is attacked,
#       give it +2 Attack PERMANENTLY.
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
    times = 3 if self.is_golden else 2
    # Summon times copies of the summoned card.
    for _ in range(times):
        minion = summoned_minion.clone(keep_buffs=True)
        board.place_minion(minion)

# TODO: Implement effect: Your cards that summon minions summon twice as many.
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

# TODO: Implement deathrattle (Add a Gold Coin to your hand).
# NOTE: This requires reading information from the C++ simulator.
WARDEN_OF_OLD = Minion(
    'Warden of Old', CardClass.NEUTRAL, MinionRace.NEUTRAL, 3, 3,
    cost=4, tier=3, abilities=CardAbility.DEATH_RATTLE | CardAbility.GENERATE
)
# TODO: Implement deathrattle (Add 2 Gold Coins to your hand).
WARDEN_OF_OLD_GOLDEN = Minion(
    'Warden of Old', CardClass.NEUTRAL, MinionRace.NEUTRAL, 6, 6,
    cost=4, tier=3, is_golden=True, abilities=CardAbility.DEATH_RATTLE | CardAbility.GENERATE
)

################################################################################
# Tier 4 cards
################################################################################
# Beast Pool

# TODO: Implement effect: Also damages the minions next to whomever this attacks.
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

# TODO: Implement deathrattle (Summon two 2/2 Hyenas).
SAVANNAH_HIGHMANE = Minion(
    'Savannah Highmane', CardClass.HUNTER, MinionRace.BEAST, 6, 5,
    cost=6, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Implement deathrattle (Summon two 4/4 Hyenas).
SAVANNAH_HIGHMANE_GOLDEN = Minion(
    'Savannah Highmane', CardClass.HUNTER, MinionRace.BEAST, 12, 10,
    cost=6, tier=4, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
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

# TODO: Implement effect: After you summon a Demon, gain +1/+1 PERMANENTLY.
BIGFERNAL = Minion(
    'Bigfernal', CardClass.NEUTRAL, MinionRace.DEMON, 4, 4,
    cost=5, tier=4
)
# TODO: Implement effect: After you summon a Demon, gain +2/+2 PERMANENTLY.
BIGFERNAL_GOLDEN = Minion(
    'Bigfernal', CardClass.NEUTRAL, MinionRace.DEMON, 8, 8,
    cost=5, tier=4, is_golden=True
)

# TODO: Implement deathrattle (Summon two 3/2 imps).
RING_MATRON = Minion(
    'Ring Matron', CardClass.WARLOCK, MinionRace.DEMON, 6, 4,
    cost=6, tier=4, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)
# TODO: Implement deathrattle (Summon two 6/4 imps).
RING_MATRON_GOLDEN = Minion(
    'Ring Matron', CardClass.WARLOCK, MinionRace.DEMON, 12, 8,
    cost=6, tier=4, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.DEATH_RATTLE
)

# TODO: Implement effect: Your other demons have +1 Attack.
SIEGEBREAKER = Minion(
    'Siegebreaker', CardClass.WARLOCK, MinionRace.DEMON, 5, 8,
    cost=7, tier=4, rarity=CardRarity.RARE, abilities=CardAbility.TAUNT
)
# TODO: Implement effect: Your other demons have +2 Attack.
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

# TODO: Implement effect: After a friendly minion loses Divine Shield, gain +2/+2.
DRAKONID_ENFORCER = Minion(
    'Drakonid Enforcer', CardClass.NEUTRAL, MinionRace.DRAGON, 3, 6,
    cost=6, tier=4
)
# TODO: Implement effect: After a friendly minion loses Divine Shield, gain +4/+4.
DRAKONID_ENFORCER_GOLDEN = Minion(
    'Drakonid Enforcer', CardClass.NEUTRAL, MinionRace.DRAGON, 6, 12,
    cost=6, tier=4, is_golden=True
)

# TODO: Implement overkill (Deal 3 damage to the left-most enemy minion).
HERALD_OF_FLAME = Minion(
    'Herald of Flame', CardClass.WARLOCK, MinionRace.DRAGON, 5, 6,
    cost=5, tier=4, abilities=CardAbility.OVERKILL
)
# TODO: Implement overkill (Deal 6 damage to the left-most enemy minion).
HERALD_OF_FLAME_GOLDEN = Minion(
    'Herald of Flame', CardClass.WARLOCK, MinionRace.DRAGON, 10, 12,
    cost=5, tier=4, is_golden=True, abilities=CardAbility.OVERKILL
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

# TODO: Implement effect: After this attacks and kills a minion,
#       deal excess damage to a random adjacent minion.
WILDFIRE_ELEMENTAL = Minion(
    'Wildfire Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 7, 3,
    cost=6, tier=4
)
# TODO: Implement effect: After this attacks and kills a minion,
#       deal excess damage to both adjacent minions.
WILDFIRE_ELEMENTAL_GOLDEN = Minion(
    'Wildfire Elemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 14, 6,
    cost=6, tier=4, is_golden=True
)

# Mech Pool
ANNOY_O_MODULE = Minion(
    'Annoy-o-Module', CardClass.PALADIN, MinionRace.MECH, 2, 4,
    cost=4, tier=4, rarity=CardRarity.RARE,
    abilities=CardAbility.MAGNETIC | CardAbility.DIVINE_SHIELD | CardAbility.TAUNT
)
ANNOY_O_MODULE_GOLDEN = Minion(
    'Annoy-o-Module', CardClass.PALADIN, MinionRace.MECH, 4, 8,
    cost=4, tier=4, rarity=CardRarity.RARE, is_golden=True,
    abilities=CardAbility.MAGNETIC | CardAbility.DIVINE_SHIELD | CardAbility.TAUNT
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

# TODO: Implement deathrattle (Summon an 8/8 Robosaur).
MECHANO_EGG = Minion(
    'Mechano-Egg', CardClass.PALADIN, MinionRace.MECH, 0, 5,
    cost=5, tier=4, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
)
# TODO: Implement deathrattle (Summon an 16/16 Robosaur).
MECHANO_EGG_GOLDEN = Minion(
    'Mechano-Egg', CardClass.PALADIN, MinionRace.MECH, 0, 10,
    cost=5, tier=4, is_golden=True, abilities=CardAbility.DEATH_RATTLE | CardAbility.SUMMON
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

# TODO: Implement effect (Whenever this minion takes damage, summon a 2/3 Mech with Taunt).
SECURITY_ROVER = Minion(
    'Security Rover', CardClass.WARLOCK, MinionRace.MECH, 2, 6,
    cost=6, tier=4, abilities=CardAbility.SUMMON
)
# TODO: Implement effect (Whenever this minion takes damage, summon a 4/6 Mech with Taunt).
SECURITY_ROVER_GOLDEN = Minion(
    'Security Rover', CardClass.WARLOCK, MinionRace.MECH, 4, 12,
    cost=6, tier=4, is_golden=True, abilities=CardAbility.SUMMON
)

# Murloc Pool

# TODO: Implement battlecry (If you control another Murloc, DISCOVER a Murloc).
# NOTE: Discover is a tricky thing to implement, so we will probably skip it!
#
# See https://www.reddit.com/r/hearthstone/comments/dzgrea/discover_mechanic/
# for details into how the discover mechanic is implemented (i.e. what pool of cards
# it selects from).
PRIMALFIN_LOOKOUT = Minion(
    'Primalfin Lookout', CardClass.NEUTRAL, MinionRace.MURLOC, 3, 3,
    cost=3, tier=4, abilities=CardAbility.BATTLECRY | CardAbility.DISCOVER,
    # _on_this_played=???
)
# TODO: Implement battlecry (If you control another Murloc, DISCOVER two Murlocs).
PRIMALFIN_LOOKOUT_GOLDEN = Minion(
    'Primalfin Lookout', CardClass.NEUTRAL, MinionRace.MURLOC, 6, 6,
    cost=3, tier=4, is_golden=True, abilities=CardAbility.BATTLECRY | CardAbility.DISCOVER,
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

# TODO: Implement effect: Whenever another friendly Pirate attacks, give it +2/+2.
RIPSNARL_CAPTAIN = Minion(
    'Ripsnarl Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 4, 5,
    cost=4, tier=4
)
# TODO: Implement effect: Whenever another friendly Pirate attacks, give it +4/+4.
RIPSNARL_CAPTAIN_GOLDEN = Minion(
    'Ripsnarl Captain', CardClass.NEUTRAL, MinionRace.PIRATE, 8, 10,
    cost=4, tier=4, is_golden=True
)

# Neutral Pool
# TODO: Implement effect: After a friendly minion loses Divine Shield, gain +2 Attack.
BOLVAR_FIREBLOOD = Minion(
    'Bolvar. Fireblood', CardClass.PALADIN, MinionRace.NONE, 1, 7,
    cost=5, tier=4, rarity=CardRarity.LEGENDARY, abilities=CardAbility.DIVINE_SHIELD
)
# TODO: Implement effect: After a friendly minion loses Divine Shield, gain +4 Attack.
BOLVAR_FIREBLOOD_GOLDEN = Minion(
    'Bolvar. Fireblood', CardClass.PALADIN, MinionRace.NONE, 2, 14,
    cost=5, tier=4, rarity=CardRarity.LEGENDARY, is_golden=True,
    abilities=CardAbility.DIVINE_SHIELD
)

# TODO: Implement effect: Whenever a friendly Taunt minion is attacked, gain +1/+1 PERMANENTLY.
CHAMPION_OF_YSHAARJ = Minion(
    'Champion of Y\'Shaarj', CardClass.NEUTRAL, MinionRace.NONE, 4, 4,
    cost=4, tier=4
)
# TODO: Implement effect: Whenever a friendly Taunt minion is attacked, gain +2/+2 PERMANENTLY.
CHAMPION_OF_YSHAARJ_GOLDEN = Minion(
    'Champion of Y\'Shaarj', CardClass.NEUTRAL, MinionRace.NONE, 8, 8,
    cost=4, tier=4, is_golden=True
)

def _defender_of_argus_on_this_played(self: Minion, board: TavernGameBoard) -> None:
    """Handle the battlecry effect for the Defender of Argus minion.
    Effect: Give adjacent minions +1/+1 (or +2/+2 if golden) and Taunt.
    """
    minions = board.get_minions_adjacent_to(self)
    for minion in minions:
        if self.is_golden:
            minion.add_buff(Buff(2, 2, CardAbility.TAUNT))
        else:
            minion.add_buff(Buff(1, 1, CardAbility.TAUNT))

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

    keys = random.sample(minions_by_race.keys(), k=min(3, len(minions_by_race)))
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

# TODO: Implement effect: After a friendly minion with Taunt dies, give its neighbours +2/+2.
QIRAJI_HARBINGER = Minion(
    'Qiraji Harbinger', CardClass.NEUTRAL, MinionRace.NONE, 5, 5,
    cost=6, tier=4
)
# TODO: Implement effect: After a friendly minion with Taunt dies, give its neighbours +4/+4.
QIRAJI_HARBINGER_GOLDEN = Minion(
    'Qiraji Harbinger', CardClass.NEUTRAL, MinionRace.NONE, 10, 10,
    cost=6, tier=4, is_golden=True
)


if __name__ == '__main__':
    import doctest
    doctest.testmod()