"""Model dataclasses for representing objects of the game."""
from __future__ import annotations

import copy
from enum import Enum, Flag, auto
from dataclasses import dataclass, field
from typing import Tuple, List, Set, Dict
from abc import ABC, abstractproperty, abstractmethod

class MinionAbility(Flag):
    """A special affect, power, or behaviour found on cards."""
    NONE = 0
    TAUNT = auto()
    DIVINE_SHIELD = auto()
    POISON = auto()
    WIND_FURY = auto()


class MinionType(Flag):
    """The type of the minion."""
    NONE = 0
    BEAST = auto()
    DEMON = auto()
    DRAGON = auto()
    MECH = auto()
    MURLOC = auto()
    NEUTRAL = auto()
    AMALGAM = BEAST | DEMON | DRAGON | MECH | MURLOC
    ALL = ~0


class MinionKeyword(Flag):
    """A keyword on a minion card."""
    NONE = 0
    TARGETED = auto()
    PLAYER_IMMUNITY = auto()
    BATTLE_CRY = auto()
    MAGNETIC = auto()
    DEATH_RATTLE = auto()
    SPECIAL_ATTACK = auto()


class AdaptationBonus(Flag):
    """An adaptation bonus.
    Adapt is an ability which allows the player to choose one of the three bonuses,
    called adaptations, for a minion from a total of ten choice cards.
    """
    ONE_ONE = auto()
    THREE_HEALTH = auto()
    THREE_ATTACK = auto()
    DIVINE_SHIELD = auto()
    TAUNT = auto()
    POSION = auto()
    DEATH_RATTLE = auto()
    WIND_FURY = auto()


class Rarity(Enum):
    """The rarity of a card."""
    CLASSIC = 'classic'
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'


class AuraType(Enum):
    """The type of the aura effect.
    An aura is an ongoing effect which grants temporary enchantments or buffs to other minions."""
    BATTLE_CRY = 'battle_cry'
    SUMMON = 'summon'
    DEATH_RATTLE = 'death_rattle'


@dataclass
class MinionTier:
    """The tier of a minion.

    Instance Attributes:
        - tier: The value of the tier.
        - num_copies: The number of copies of a minion with this tier.
    """
    tier: int = 1
    num_copies: int = 1


# A dict mapping each tier rank to a MinionTier instance.
TIER_RANKS = {
    1: MinionTier(1, 18),
    2: MinionTier(2, 15),
    3: MinionTier(3, 13),
    4: MinionTier(4, 11),
    5: MinionTier(5, 9),
    6: MinionTier(6, 6)
}


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
        - name: The name of the card.
        - rarity: The rarity of the card.
        - cost: The mana cost of the card.
        - type: The type of the minion.
        - tier: The tier of this minion.
        - abilities: The abilities of this minion.
                     This consists of a combination of the MinionAbility flags.
        - keywords: The keywords of this minion.
                    This consists of a combination of the MinionKeyword flags.
        - valid_targets: The type of minions this minion can target.
        - num_copies: The number of copies to make of this minion.
        - level: The level of this minion.
        - health: The health of this minion.
        - attack: The attack of this minion.
        - in_pool: Whether this minion is in the pool.
        - parent_minion: The parent of this minion (used when a minion creates a new one).
    """
    # Private Instance Attributes:
    #   - _damage_taken: The amount of damage the minion has taken.
    #   - _temp_buffs: A set of buffs appplied to this minion.
    name: str
    type: MinionType
    health: int
    attack: int
    num_copies: int

    cost: int = 1
    rarity: Rarity = Rarity.COMMON
    tier: MinionTier = TIER_RANKS[1]
    level: int = 1

    abilities: MinionAbility = MinionAbility.NONE
    keywords: MinionKeyword = MinionKeyword.NONE
    valid_targets: MinionType = MinionType.ALL

    in_pool: bool = True
    parent_minion: Optional[Minion] = None

    _damage_taken: int = 0
    _temp_buffs: List[Buff] = field(default_factory=list)

    # TODO: Add event system for minion callbacks (i.e. on death, on turn start, etc...)

    @property
    def current_health(self) -> int:
        """Return the current health of this minion."""
        total_health = self.health + sum(buff.health for buff in self._temp_buffs)
        return total_health - self._damage_taken

    @property
    def current_attack(self) -> int:
        """Return the current attack of this minion."""
        return self.attack + sum(buff.attack for buff in self._temp_buffs)

    @property
    def current_abilities(self) -> MinionAbility:
        """Return the current abilities of this minion."""
        current_abilities = self.abilities
        for buff in self._temp_buffs:
            current_abilities |= buff.abilities
        return current_abilities

    def take_damage(self, damage: int) -> Tuple[bool, bool, bool, bool]:
        """Inflict the given amount of damage onto this minion.

        Return a 4-tuple of booleans values consisting of whether this minion
        took damage, lost divine shield, overkilled, and/or whether this minion is dead.

        >>> minion = Minion('Mario', MinionType.NEUTRAL, 3, 1, 1)  # Create a minion with 3 health.
        >>> minion.abilities |= MinionAbility.DIVINE_SHIELD  # Give the minion divine shield
        >>> minion.take_damage(100)
        (False, True, False, False)
        >>> minion.current_health
        3
        >>> minion.take_damage(2)
        (True, False, False, False)
        >>> minion.current_health
        1
        >>> minion.take_damage(2)
        (True, False, True, True)
        >>> minion.current_health
        -1
        """
        if damage == 0:
            return False, False, False, False

        if MinionAbility.DIVINE_SHIELD in self.abilities:
            # Clear divine shield, since we've taken damage.
            self.abilities &= ~MinionAbility.DIVINE_SHIELD
            return False, True, False, False

        self._damage_taken += damage
        current_health = self.current_health
        return True, False, current_health < 0, current_health <= 0

    def add_buff(self, buff: Buff) -> None:
        """Apply the given buff to this minion whose source is the given minion.

        >>> minion = Minion('Lonely Boy', MinionType.DEMON, 0, 0, 1)  # A lonely minion.
        >>> buff = Buff(health=1, attack=2, abilities=MinionAbility.TAUNT |\
                                                      MinionAbility.DIVINE_SHIELD)
        >>> minion.add_buff(buff)
        >>> minion.current_health == 1 and minion.current_attack == 2
        True
        >>> MinionAbility.TAUNT in minion.current_abilities and \
            MinionAbility.DIVINE_SHIELD in minion.current_abilities
        True
        """
        self._temp_buffs.append(buff)

    def remove_buff(self, buff: Buff) -> None:
        """Remove the given buff.
        Do nothing if the given buff is not applied to this minion.

        >>> minion = Minion('Lonely Boy', MinionType.DEMON, 0, 0, 1)  # A lonely minion.
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
        self._damage_taken = max(self._damage_taken - buff.health, 0)
        self._temp_buffs.remove(buff)

    def clone(self, keep_buffs: bool = False) -> Minion:
        """Return a clone of this minion.

        Args:
            keep_buffs: Whether to keep the buffs applied to this minion.
        """
        minion_copy = copy.copy(self)
        if not keep_buffs:
            # Clear buffs
            minion_copy._temp_buffs = dict()
        return minion_copy


if __name__ == '__main__':
    import doctest
    doctest.testmod()