"""Model dataclasses for representing objects of the game."""
from enum import Enum, Flag, auto
from dataclasses import dataclass


class Ability(Flag):
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