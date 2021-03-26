"""Implementation of various minion cards.

These minions are implemented for Hearthstone Patch 20.0.
Data Source: https://hearthstone.fandom.com/wiki/Battlegrounds#Minions_by_tier
"""
import random
import logging
from typing import Dict

from hsbg.models import CardClass, CardRarity, CardAbility, MinionRace, Buff, Minion


def get_all_minions(gold_suffix: str = '_golden') -> Dict[str, Minion]:
    """Return a dict mapping the name of a minion to its instance.
    The key is the name of the minion (with an additional suffix if the minion is golden).

    Args:
        gold_suffix: The suffix to add to keys representing minions that are golden.
    """
    all_minions = {}
    globals_copy = globals().copy()
    for obj in globals_copy.values():
        if not isinstance(obj, Minion):
            continue
        key = obj.name + (gold_suffix if obj.is_golden else '')

        # Warn the user if duplicate minions were found!
        if key in all_minions:
            logging.warn(f'Found duplicate minion (\'{key}\')')

        all_minions[key] = obj
    return all_minions


################################################################################
# Tier 1 cards
################################################################################
# Beast Pool

# Tabbycat summoned by Alleycat
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
    if MinionRace.DEMON not in ctx.played_minion.race:
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

# Water Droplet generated by Sellemental
WATER_DROPLET = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 2, 2,
    cost=3, purchasable=False
)
WATER_DROPLET_GOLDEN = Minion(
    'Water Droplet', CardClass.NEUTRAL, MinionRace.ELEMENTAL, 4, 4,
    cost=3, is_golden=True, purchasable=False
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
    """Handle the Micro Mummy effect on the end of a turn.
    Effect: At the end of your turn, give another random friendly
    minion +1 (or +2 if golden) Attack.
    """
    minion = ctx.board.get_random_minion(kind='friendly', ignore=[self])
    if minion is None:
        return
    if self.is_golden:
        minion.add_buff(Buff(2, 0, CardAbility.NONE))
    else:
        minion.add_buff(Buff(1, 0, CardAbility.NONE))

# NOTE: only reborn card in game!
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
    if MinionRace.MURLOC not in ctx.summoned_minion.race:
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
    minion = ctx.board.get_random_minion(race=MinionRace.MURLOC, kind='friendly', ignore=[self])
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

def _pack_leader_on_card_summoned(self, ctx) -> None:
    """Handle the Pack Leader effect.
    Effect: Whenever you summon a Beast, give it +2 (or +4 if golden) Attack."""
    if MinionRace.BEAST not in ctx.summoned_minion.race:
        return
    if self.is_golden:
        ctx.summoned_minion.add_buff(Buff(4, 0, CardAbility.NONE))
    else:
        ctx.summoned_minion.add_buff(Buff(2, 0, CardAbility.NONE))

PACK_LEADER = Minion(
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 2, 3,
    cost=2, tier=2, rarity=CardRarity.RARE,
    _on_card_summoned=_pack_leader_on_card_summoned
)
PACK_LEADER_GOLDEN = Minion(
    'Pack Leader', CardClass.NEUTRAL, MinionRace.BEAST, 4, 6,
    cost=2, tier=2, rarity=CardRarity.RARE, is_golden=True,
    _on_card_summoned=_pack_leader_on_card_summoned
)

def _rabid_saurolisk_on_any_played(self, ctx) -> None:
    """Handle the Rabid Saurolisk effect.
    Effect: After you play a minion with Deathrattle, gain +1/+2 (or +2/+4 if golden).
    """
    if CardAbility.DEATH_RATTLE not in ctx.played_minion.abilities:
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

def _nathrezim_overseer_on_this_played(self, ctx) -> None:
    """Handle the Nathrezim Overseer battlecry effect.
    Effect: Give a friendly Demon +2/+2 (or +4/+4 if golden).

    Note: the demon is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Demon
    minion = ctx.board.get_random_minion(race=MinionRace.DEMON, kind='friendly', ignore=[self])
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
# TODO: Implement effect: Whenever this attacks, DOUBLR its attack.
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

def _steward_of_time_on_this_sold(self, ctx) -> None:
    """Handle the effect for the Steward of Time minion.
    Effect: When you sell this minion, give all minions in Bob's Tavern +1/+1 (or +2/+2 if golden).
    """
    for minion in ctx.board.get_minions():
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
def _molten_rock_on_any_played(self, ctx) -> None:
    """Handle the effect for the Molten Rock minion.
    Effect: After you play an Elemental, gain +1 (or +2 if golden) Health.
    """
    if MinionRace.ELEMENTAL not in ctx.played_minion.race:
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

def _party_elemental_on_any_played(self, ctx) -> None:
    """Handle the effect for the Party Elemental minion.
    Effect: After you play an Elemental, give another random friendly Elemental +1/+1
    (or +2/+2 if golden).

    Note: the elemental is chosen RANDOMLY since we do not have targetting implemented.
    """
    if MinionRace.ELEMENTAL not in ctx.played_minion.race:
        return

    times = 2 if self.is_golden else 1
    for _ in range(times):
        minion = ctx.board.get_random_minion(race=MinionRace.ELEMENTAL,
                                             kind='friendly', ignore=[self])
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

def _metaltooth_leaper_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Metaltooth Leaper minion.
    Effect: Give your other Mechs +2 (or +4 if golden) Attack.
    """
    additional_attack = 4 if self.is_golden else 2
    minions = ctx.board.get_minions(race=MinionRace.MECH, ignore=[self])
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
    _on_this_sold=lambda self, ctx: ctx.give_gold(abs(3 - ctx.current_sell_price))
)
FREEDEALING_GAMBLER_GOLDEN = Minion(
    'Freedealing Gambler', CardClass.NEUTRAL, MinionRace.PIRATE, 6, 6,
    cost=3, tier=2, is_golden=True,
    # Effect: This minion sells for 6 golds.
    _on_this_sold=lambda self, ctx: ctx.give_gold(abs(6 - ctx.current_sell_price))
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
def _managerie_mug_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Menagerie Mug effect.
    Effect: Give 3 random friendly minions of different minion types +1/+1 (or +2/+2 if golden).
    """
    for minion in ctx.board.get_minions(kind='friendly', ignore=[self]):
        if minion.race not in minions_by_race:
            minions_by_race[minion.race] = []
        minions_by_race[minion.race].append(minion)

    keys = random.sample(minions.keys(), k=3)
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

def _houndmaster_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Houndmaster minion.
    Effect: Give a friendly Beast +2/+2 (or +4/+4 if golden) and Taunt.

    Note: the beast is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Beast
    minion = ctx.board.get_random_minion(race=MinionRace.BEAST, kind='friendly', ignore=[self])
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

def _crystal_weaver_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Crystalweaver minion.
    Effect: Give your Demons +1/+1 (or +2/+2 if golden).
    """
    minions = ctx.board.get_minions(race=MinionRace.DEMON)
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

def _soul_devourer_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Soul Devourer minion.
    Effect (regular): Choose a friendly Demon. Remove it to gain its stats and 3 gold.
    Effect (golden):  Choose a friendly Demon. Remove it to gain double its stats and 6 gold.
    """
    minion = ctx.board.get_random_minion(race=MinionRace.DEMON, kind='friendly', ignore=[self])
    # Remove minion from board
    ctx.board.remove_minion(minion)

    multiplier = 2 if self.is_golden else 1
    attack_buff = minion.current_attack * multiplier
    health_buff = minion.current_health * multiplier

    # Give stats to self
    self.add_buff(Buff(attack_buff, health_buff, CardAbility.NONE))
    # Give gold
    ctx.board.give_gold(3 * multiplier)

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

def _hangry_dragon_on_new_turn(self, ctx) -> None:
    """Handle the effect for the Hangry Dragon minion.
    Effect: At the start of your turn, gain +2/+2 (or +4/+4 if golden) if you won the last combat.
    """
    if not ctx.board.won_previous:
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

def _twilight_emissary_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Twilight Emissary minion.
    Effect: Give a friendly Dragon +2/+2 (or +4/+4 if golden).

    Note: the dragon is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Murloc
    minion = ctx.board.get_random_minion(race=MinionRace.DRAGON, kind='friendly', ignore=[self])
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
def _arcane_assistant_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Arcane Assistant minion.
    Effect: Give your Elementals +1/+1 (or +2/+2 if golden).
    """
    buff_amount = 2 if self.is_golden else 1
    minions = ctx.board.get_minions(race=MinionRace.ELEMENTAL, ignore=[self])
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

def _iron_sensei_on_end_turn(self, ctx) -> None:
    """Handle the effect for the Iron Sensei minion.
    Effect: At the end of your turn, give another friendly Mech +2/+2 (or +4/+4 if golden).

    Note: the mech is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Mech
    minion = ctx.board.get_random_minion(race=MinionRace.MECH, kind='friendly', ignore=[self])
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

def _screwjank_clunker_on_this_played(self, ctx) -> None:
    """Handle the battlecry effect for the Screwjank Clunker minion.
    Effect: Give a friendly Mech +2/+2 (or +4/+4 if golden).

    Note: the mech is chosen RANDOMLY since we do not have targetting implemented.
    """
    # Choose a random friendly Mech
    minion = ctx.board.get_random_minion(race=MinionRace.MECH, kind='friendly', ignore=[self])
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
