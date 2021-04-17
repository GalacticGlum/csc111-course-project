"""Model dataclasses for representing objects of the game.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
from __future__ import annotations
import copy
from enum import Enum, Flag, auto
from dataclasses import dataclass, field
from typing import List, Optional, Callable


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

    @classmethod
    def from_name(cls, name: str) -> Optional[CardClass]:
        """Return the CardClass with the given name. This is case sensitive."""
        try:
            return cls[name]
        except KeyError:
            return None


class CardRarity(Enum):
    """The rarity of a card."""
    CLASSIC = 'classic'
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'

    @classmethod
    def from_name(cls, name: str) -> Optional[CardRarity]:
        """Return the CardRarity with the given name. This is case sensitive."""
        try:
            return cls[name]
        except KeyError:
            return None


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

    @classmethod
    def from_name(cls, name: str) -> Optional[MinionRace]:
        """Return the MinionRace with the given name. This is case sensitive."""
        try:
            return cls[name]
        except KeyError:
            return None


class CardAbility(Flag):
    """A special affect, power, or behaviour found on cards."""
    NONE = 0
    TAUNT = auto()
    DIVINE_SHIELD = auto()
    POISONOUS = auto()
    WINDFURY = auto()
    MEGA_WINDFURY = auto()
    BATTLECRY = auto()
    DEATH_RATTLE = auto()
    REBORN = auto()

    def as_format_str(self) -> str:
        """Return this CardAbility as a properly formatted string.

        >>> CardAbility.NONE.as_format_str()
        'None'
        >>> CardAbility.DIVINE_SHIELD.as_format_str()
        'Divine Shield'
        >>> CardAbility.MEGA_WINDFURY.as_format_str()
        'Mega Windfury'
        """
        name = self.name.replace('_', ' ')
        parts = name.split()
        return ' '.join(x[0].upper() + x[1:].lower() for x in parts)


# A list of abilities that are also mechanics
MECHANIC_ABILITIES = [
    CardAbility.TAUNT,
    CardAbility.DIVINE_SHIELD,
    CardAbility.POISONOUS,
    CardAbility.WINDFURY,
    CardAbility.REBORN
]


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
    abilities: CardAbility


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
    #   - _on_this_summoned: A function called when this card is summoned.
    #   - _on_any_summoned: A function called when a card is summoned.
    #   - _on_new_turn: A function called on the start of a new turn.
    #   - _on_end_turn: A function called on the start of a new turn.
    name: str
    card_class: CardClass
    race: MinionRace
    attack: int
    health: int
    cost: int = 1
    rarity: CardRarity = CardRarity.COMMON
    tier: int = 1

    is_golden: bool = False
    abilities: CardAbility = CardAbility.NONE

    purchasable: bool = True
    _buffs: List[Buff] = field(default_factory=list)

    # Events
    _on_this_bought: Optional[Callable[[Minion, TavernGameBoard], None]] = None
    _on_this_sold: Optional[Callable[[Minion, TavernGameBoard], None]] = None
    _on_this_played: Optional[Callable[[Minion, TavernGameBoard], None]] = None
    _on_any_played: Optional[Callable[[Minion, TavernGameBoard, Minion], None]] = None
    _on_this_summoned: Optional[Callable[[Minion, TavernGameBoard], None]] = None
    _on_any_summoned: Optional[Callable[[Minion, TavernGameBoard, Minion], None]] = None
    _on_new_turn: Optional[Callable[[Minion, TavernGameBoard], None]] = None
    _on_end_turn: Optional[Callable[[Minion, TavernGameBoard], None]] = None

    @property
    def buffs(self) -> List[Buff]:
        """Return the list of buffs of this minion."""
        return self._buffs

    @property
    def current_health(self) -> int:
        """Return the current health of this minion (including buffs)."""
        return self.health + sum(buff.health for buff in self._buffs)

    @property
    def current_attack(self) -> int:
        """Return the current attack of this minion (including buffs)."""
        return self.attack + sum(buff.attack for buff in self._buffs)

    @property
    def current_abilities(self) -> CardAbility:
        """Return the current abilities of this minion (including buffs)."""
        result = self.abilities
        for buff in self._buffs:
            result |= buff.abilities
        return result

    def add_buff(self, buff: Buff) -> None:
        """Apply the given buff to this minion whose source is the given minion.

        >>> minion = Minion('Lonely Boy', CardClass.NEUTRAL, \
        MinionRace.DEMON, 0, 0)  # A lonely minion.
        >>> buff = Buff(health=1, attack=2, abilities=CardAbility.TAUNT |\
                                                      CardAbility.DIVINE_SHIELD)
        >>> minion.add_buff(buff)
        >>> minion.current_health == 1 and minion.current_attack == 2
        True
        >>> CardAbility.TAUNT in minion.current_abilities and \
            CardAbility.DIVINE_SHIELD in minion.current_abilities
        True
        """
        self._buffs.append(buff)

    def remove_buff(self, buff: Buff) -> None:
        """Remove the given buff.
        Do nothing if the given buff is not applied to this minion.

        >>> minion = Minion('Lonely Boy', CardClass.NEUTRAL, \
        MinionRace.DEMON, 0, 0)  # A lonely minion.
        >>> buff = Buff(health=1, attack=2, abilities=CardAbility.TAUNT |\
                                                      CardAbility.DIVINE_SHIELD)
        >>> minion.add_buff(buff)
        >>> minion.remove_buff(buff)
        >>> minion.current_health == 0 and minion.current_attack == 0
        True
        >>> minion.current_abilities == CardAbility.NONE
        True
        """
        if buff not in self._buffs:
            return
        self._buffs.remove(buff)

    def clone(self, keep_buffs: bool = False) -> Minion:
        """Return a clone of this minion.

        Args:
            keep_buffs: Whether to keep the buffs applied to this minion.

        >>> minion = Minion('Lonely Boy', CardClass.NEUTRAL, \
        MinionRace.DEMON, 0, 0) # A lonely minion.
        >>> copy_minion = minion.clone()
        >>> minion is copy_minion
        False
        """
        minion_copy = copy.copy(self)
        if not keep_buffs:
            # Clear buffs
            minion_copy._buffs = []
        return minion_copy

    def on_this_bought(self, board: TavernGameBoard) -> None:
        """Handle when THIS minion is bought."""
        if self._on_this_bought is not None:
            self._on_this_bought(self, board)

    def on_this_sold(self, board: TavernGameBoard) -> None:
        """Handle when THIS minion is sold."""
        if self._on_this_sold is not None:
            self._on_this_sold(self, board)

    def on_this_played(self, board: TavernGameBoard) -> None:
        """Handle when THIS minion is played from the hand."""
        if self._on_this_played is not None:
            self._on_this_played(self, board)

    def on_any_played(self, board: TavernGameBoard, played_minion: Minion) -> None:
        """Handle when ANY minion is played from the hand."""
        if self._on_any_played is not None:
            self._on_any_played(self, board, played_minion)

    def on_this_summoned(self, board: TavernGameBoard) -> None:
        """Handle when THIS minion is summoned onto the board."""
        if self._on_this_summoned is not None:
            self._on_this_summoned(self, board)

    def on_any_summoned(self, board: TavernGameBoard, summoned_minion: Minion) -> None:
        """Handle when ANY minion is summoned onto the board."""
        if self._on_any_summoned is not None:
            self._on_any_summoned(self, board, summoned_minion)

    def on_new_turn(self, board: TavernGameBoard) -> None:
        """Handle the start of a turn."""
        if self._on_new_turn is not None:
            self._on_new_turn(self, board)

    def on_end_turn(self, board: TavernGameBoard) -> None:
        """Handle the end of a turn."""
        if self._on_end_turn is not None:
            self._on_end_turn(self, board)

    def __str__(self) -> str:
        """Return a string representation of this minion.

        >>> from hsbg import minions
        >>> from hsbg.models import CardAbility
        >>> str(minions.MURLOC_SCOUT)
        '1/1 Murloc Scout'
        >>> minion = minions.CRYSTAL_WEAVER.clone()
        >>> minion.add_buff(Buff(10, 3, CardAbility.TAUNT))
        >>> str(minion)
        '15/7 Crystalweaver, taunt'
        """
        buffs = [
            ability.as_format_str().lower() for ability in MECHANIC_ABILITIES
            if ability in self.current_abilities
        ]

        name = ('golden ' if self.is_golden else '') + self.name
        name_and_buffs = ', '.join([name] + buffs)
        return f'{self.current_attack}/{self.current_health} {name_and_buffs}'


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['copy', 'enum'],
    #     'allowed-io': [],
    #     'max-line-length': 100,
    #     'disable': ['E1136', 'E0602', 'E1101', 'R0902', 'E9959', 'E9972', 'E9997']
    # })
    #
    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()
