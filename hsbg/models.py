"""Model dataclasses for representing objects of the game."""
from __future__ import annotations

import copy
from enum import Enum, Flag, auto
from typing import List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractproperty, abstractmethod


class CardClass(Enum):
    """The class of a card."""
    DEMON_HUNTER = 'demon_hunter'
    DRUID = 'druid'
    HUNTER = 'hunter'
    MAGE = 'mage'
    PALADIN = 'paladin'
    PRIEST = 'priest'
    ROGUE = 'rogue'
    SHAMAN = 'shaman'
    WARLOCK = 'warlock'
    WARRIOR = 'warrior'
    DEATH_KNIGHT = 'death_knight'
    NEUTRAL = 'neutral'


class CardRarity(Enum):
    """The rarity of a card."""
    CLASSIC = 'classic'
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'


class CardAbility(Flag):
    """A special affect, power, or behaviour found on cards."""
    NONE = 0
    TAUNT = auto()
    DIVINE_SHIELD = auto()
    POISON = auto()
    WINDFURY = auto()
    MEGA_WINDFURY = auto()
    BATTLECRY = auto()
    DEATH_RATTLE = auto()
    START_OF_COMBAT = auto()
    SUMMON = auto()
    GENERATE = auto()
    REBORN = auto()
    CHARGE = auto()


class MinionRace(Flag):
    """The race of the minion."""
    NONE = 0
    BEAST = auto()
    DEMON = auto()
    DRAGON = auto()
    MECH = auto()
    MURLOC = auto()
    ELEMENTAL = auto()
    PIRATE = auto()
    NEUTRAL = auto()
    AMALGAM = BEAST | DEMON | DRAGON | MECH | MURLOC
    ALL = ~0


# class MinionKeyword(Flag):
#     """A keyword on a minion card."""
#     NONE = 0
#     TARGETED = auto()
#     PLAYER_IMMUNITY = auto()
#     BATTLECRY = auto()
#     MAGNETIC = auto()
#     DEATH_RATTLE = auto()
#     SPECIAL_ATTACK = auto()


@dataclass
class Buff:
    """A buff.

    Instance Attributes:
        - attack: The additional attack provided by this buff.
        - health: The additional health provided by this buff.
        - abilities: Additional abilities provided by this buff.
    """
    attack: int
    health: int
    abilities: MinionAbility


@dataclass
class Minion:
    """A minion.

    Instance Attributes:
        - name: The name of this minion.
        - card_class: The type of this minion.
        - race: The race of this minion.
        - health: The health of this minion.
        - attack: The attack of this minion.
        - cost: The mana cost of this minion.
        - rarity: The rarity of this minion.
        - tier: The tier of this minion.
        - is_golden: Whether this minion is a golden copy.
        - abilities: The abilities of this minion.
                     This consists of a combination of the CardAbility flags.
        - purchasable: Whether this minion is in the card pool (i.e. can it be purchased).
    """
    # Private Instance Attributes:
    #   - _buffs: A set of buffs appplied to this minion.
    #   - _on_this_bought: A function called when this minion is bought.
    #   - _on_this_sold: A function called when this minion is sold.
    #   - _on_this_played: A function called when this minion is played from the hand.
    #   - _on_any_played: A function called when any card is played from the hand.
    #   - _on_card_summoned: A function called when a card is summoned.
    #   - _on_new_turn: A function called on the start of a new turn.
    #   - _on_end_turn: A function called on the start of a new turn.
    name: str
    card_class: CardClass
    race: MinionRace
    health: int
    attack: int
    cost: int = 1
    rarity: CardRarity = CardRarity.COMMON
    tier: int = 1

    is_golden: bool = False
    abilities: MinionAbility = CardAbility.NONE

    purchasable: bool = True
    _buffs: List[Buff] = field(default_factory=list)

    # Events
    _on_this_bought: Optional[callable] = None
    _on_this_sold: Optional[callable] = None
    _on_this_played: Optional[callable] = None
    _on_any_played: Optional[callable] = None
    _on_card_summoned: Optional[callable] = None
    _on_new_turn: Optional[callable] = None
    _on_end_turn: Optional[callable] = None

    @property
    def current_health(self) -> int:
        """Return the current health of this minion (including buffs)."""
        total_health = self.health + sum(buff.health for buff in self._buffs)
        return total_health

    @property
    def current_attack(self) -> int:
        """Return the current attack of this minion (including buffs)."""
        return self.attack + sum(buff.attack for buff in self._buffs)

    @property
    def current_abilities(self) -> MinionAbility:
        """Return the current abilities of this minion (including buffs)."""
        current_abilities = self.abilities
        for buff in self._buffs:
            current_abilities |= buff.abilities
        return current_abilities

    def add_buff(self, buff: Buff) -> None:
        """Apply the given buff to this minion whose source is the given minion.

        >>> minion = Minion('Lonely Boy', MinionRace.DEMON, 0, 0)  # A lonely minion.
        >>> buff = Buff(health=1, attack=2, abilities=MinionAbility.TAUNT |\
                                                      MinionAbility.DIVINE_SHIELD)
        >>> minion.add_buff(buff)
        >>> minion.current_health == 1 and minion.current_attack == 2
        True
        >>> MinionAbility.TAUNT in minion.current_abilities and \
            MinionAbility.DIVINE_SHIELD in minion.current_abilities
        True
        """
        self._buffs.append(buff)

    def remove_buff(self, buff: Buff) -> None:
        """Remove the given buff.
        Do nothing if the given buff is not applied to this minion.

        >>> minion = Minion('Lonely Boy', MinionRace.DEMON, 0, 0)  # A lonely minion.
        >>> buff = Buff(health=1, attack=2, abilities=MinionAbility.TAUNT |\
                                                      MinionAbility.DIVINE_SHIELD)
        >>> minion.add_buff(buff)
        >>> minion.remove_buff(buff)
        >>> minion.current_health == 0 and minion.current_attack == 0
        True
        >>> minion.current_abilities == MinionAbility.NONE
        True
        """
        if buff not in self._temp_buffs:
            return
        self._buffs.remove(buff)

    def clone(self, keep_buffs: bool = False) -> Minion:
        """Return a clone of this minion.

        Args:
            keep_buffs: Whether to keep the buffs applied to this minion.

        >>> minion = Minion('Lonely Boy', MinionRace.DEMON, 0, 0)  # A lonely minion.
        >>> copy_minion = minion.clone()
        >>> minion is copy_minion
        False
        """
        minion_copy = copy.copy(self)
        if not keep_buffs:
            # Clear buffs
            minion_copy._buffs = dict()
        return minion_copy

    def on_this_played(self, ctx: Any) -> None:
        """Handle when THIS minion is played from the hand.
        Mutates the given game state.
        """
        if self._on_this_played is not None:
            self._on_this_played(self, ctx)

    def on_any_played(self, ctx: Any) -> None:
        """Handle when ANY minion is played from the hand.
        Mutates the given game state.
        """
        if self._on_any_played is not None:
            self._on_any_played(self, ctx)


if __name__ == '__main__':
    import doctest
    doctest.testmod()