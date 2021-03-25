"""Implementation of various minion cards.

These minions are implemented for Hearthstone Path 20.0.
Data Source: https://hearthstone.fandom.com/wiki/Battlegrounds#Minions_by_tier
"""
from typing import Dict

from hsbg.models import CardClass, CardRarity, CardAbility, MinionRace, Buff, Minion


def get_all_minions(gold_suffix: str = '_golden') -> Dict[str, Minion]:
    """Return a dict mapping the name of a minion to its instance.
    The key is the name of the minion (with an additional suffix if the minion is golden).

    Args:
        gold_suffix: The suffix to add to keys representing minions that are golden.
    """
    all_minions = {}
    for obj in globals().values():
        if not isinstance(obj, Minion):
            continue
        key = obj.name + (gold_suffix if obj.is_golden else '')
        all_minions[key] = obj
    return all_minions


################################################################################
# Tier 1 cards
################################################################################
# Beast Pool
TABBY_CAT = Minion(
    'Tabbycat', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    purchasable=False
)
TABBY_CAT_GOLDEN = Minion(
    'Tabbycat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    is_golden=True, purchasable=False
)

ALLEY_CAT = Minion(
    'Alleycat', CardClass.HUNTER, MinionRace.BEAST, 1, 1,
    abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, ctx: ctx.board.summon('Tabbycat', is_golden=False)
)
ALLEY_CAT_GOLDEN = Minion(
    'Alleycat', CardClass.HUNTER, MinionRace.BEAST, 2, 2,
    is_golden=True, abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, ctx: ctx.board.summon('Tabbycat', is_golden=True)
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
    _on_this_played=lambda self, ctx: ctx.board.attack_hero(2, kind='friendly')
)
VULGAR_HOMUNCULUS_GOLDEN = Minion(
    'Vulgar Homunculus', CardClass.WARLOCK, MinionRace.DEMON, 4, 8,
    cost=2, is_golden=True, abilities=CardAbility.TAUNT | CardAbility.BATTLECRY,
    _on_this_played=lambda self, ctx: ctx.board.attack_hero(2, kind='friendly')
)

def _wrath_weaver_on_any_played(self, ctx) -> None:
    """Handle the effect for the Wrath Weaver minion when a card is played from the hand.
    Effect: After you play a demon, deal 1 damage to your hero, and gain +2/+2 (or +4/+4 if golden).
    """
    if MinionRace.DEMON not in ctx.played_card.race:
        return
    if self.is_golden:
        buff = Buff(2, 2, CardAbility.NONE)
    else:
        buff = Buff(4, 4, CardAbility.NONE)

    ctx.board.attack_hero(1, kind='friendly')
    self.add_buff(buff)

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
    _on_this_played=lambda self, ctx: ctx.modify_refresh_cost(0, times=1)
)
REFRESHING_ANOMALY_GOLDEN = Minion(
    'Refreshing Anomaly', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 6,
    is_golden=True, abilities=CardAbility.BATTLECRY,
    _on_this_played=lambda self, ctx: ctx.modify_refresh_cost(0, times=2)
)

WATER_DROPLET = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, purchasable=False
)
WATER_DROPLET_GOLDEN = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=3, purchasable=False, is_golden=True
)

SELLEMENTAL = Minion(
    'Sellemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, abilities=CardAbility.GENERATE,
    _on_this_sold=lambda self, ctx: ctx.board.add_card_to_hand('Water Droplet', num=1)
)
SELLEMENTAL_GOLDEN = Minion(
    'Sellemental', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, abilities=CardAbility.GENERATE, is_golden=True,
    _on_this_sold=lambda self, ctx: ctx.board.add_card_to_hand('Water Droplet', num=2)
)

# Mech Pool
MICRO_MACHINE = Minion(
    'Micro Machine', CardClass.NEUTRAL, MinionRace.MECH, 1, 2,
    cost=2,
    _on_new_turn=lambda self, ctx: self.add_buff(Buff(1, 0, CardAbility.NONE))
)
MICRO_MACHINE_GOLDEN = Minion(
    'Micro Machine', CardClass.NEUTRAL, MinionRace.MECH, 2, 4,
    cost=2, is_golden=True,
    _on_new_turn=lambda self, ctx: self.add_buff(Buff(2, 0, CardAbility.NONE))
)

def _micro_mummy_on_end_turn(self, ctx) -> None:
    """Handle the Micro Mummy reborn effect on the end of a turn.
    Effect: At the end of your turn, give another random friendly
    minion +1 (or +2 if golden) Attack.
    """
    minion = ctx.board.get_random_minion(kind='friendly')
    if minion == self or minion is None:
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
def _murloc_tidecaller_on_card_summoned(self, ctx) -> None:
    """Handle the Murloc Tidecaller effect.
    Effect: Whenever you summon a Murloc, gain +1 (or +2 if golden) Attack."""
    if MinionRace.MURLOC not in ctx.summoned_card.race:
        return
    if self.is_golden:
        self.add_buff(Buff(2, 0, CardAbility.NONE))
    else:
        self.add_buff(Buff(1, 0, CardAbility.NONE))

MURLOC_TIDECALLER = Minion(
    'Murloc Tidecaller', CardClass.NEUTRAL, MinionRace.MURLOC, 1, 2,
    rarity=CardRarity.RARE,
    _on_card_summoned=_murloc_tidecaller_on_card_summoned
)
MURLOC_TIDECALLER_GOLDEN = Minion(
    'Murloc Tidecaller', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 4,
    rarity=CardRarity.RARE, is_golden=True,
    _on_card_summoned=_murloc_tidecaller_on_card_summoned
)

MURLOC_TIDEHUNTER = Minion(
    'Murloc Tidehunter', CardClass.NEUTRAL, MinionRace.MURLOC, 2, 1,
    abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, ctx: ctx.board.summon('Murloc Scout', is_golden=False)
)
MURLOC_TIDEHUNTER_GOLDEN = Minion(
    'Murloc Tidehunter', CardClass.NEUTRAL, MinionRace.MURLOC, 4, 2,
    cost=2, is_golden=True, abilities=CardAbility.BATTLECRY | CardAbility.SUMMON,
    _on_this_played=lambda self, ctx: ctx.board.summon('Murloc Scout', is_golden=True)
)

def _rockpool_hunter_on_this_played(self, ctx) -> None:
    """Handle the Rockpool Hunter battlecry effect.
    Effect: Give a friendly Murloc +1/+1 (or +2/+2 if golden).

    Note: the murloc is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Murloc
    minion = ctx.board.get_random_minion(race=MinionRace.MURLOC, kind='friendly')
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
def _deck_swabbie_on_this_played(self, ctx) -> None:
    """Handle the Deck Swabbie battlecry effect.
    Effect: Reduce the cost of upgrading Bob's Tavern by (1) (or (2) if golden).
    """
    cost = ctx.board.current_tavern_upgrade_cost
    discount = 2 if self.is_golden else 1
    ctx.board.modify_tavern_upgrade_cost(cost - discount, times=1)

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
