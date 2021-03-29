"""A simulator for Hearthstone Battlegrounds."""
from typing import List, Optional

from hsbg.minions import Minion

# The maximum number of minions a player can have in their hand.
MAX_HAND_SIZE = 10
# The maximum number of minions that can be on the board in a tavern.
MAX_TAVERN_BOARD_SIZE = 7
# The maximum number of recruits that can be on the board in a tavern.
MAX_TAVERN_RECRUIT_SIZE = 6
# The maximum number of gold the player can have.
MAX_TAVERN_GOLD = 10
# The amount of gold the player gets per turn.
GOLD_PER_TURN = 1

# A dict mapping each tavern tier to its upgrade cost.
# The element at index i indicates the cost of upgrading FROM a tavern with tier i.
TAVERN_UPGRADE_COSTS = [
    0,  # Padding element
    5,  # Cost of upgrading from tier 1 (5 gold)
    7,  # Cost of upgrading from tier 2 (7 gold)
    8,  # Cost of upgrading from tier 3 (8 gold)
    9,  # Cost of upgrading from tier 4 (9 gold)
    10  # Cost of upgrading from tier 5 (10 gold)
]
# The maximum tavern tier
MAX_TAVERN_TIER = 6


class TavernGameBoard:
    """A class representing the state of a tavern game board for a single player."""
    # Private Instance Attributes:
    #   - _turn_number: The current turn (where 1 indicates the first turn).
    #   - _hero_health: The current health of the hero.
    #   - _tavern_tier: The current tier of the tavern.
    #   - _gold: The current gold that the player has.
    #   - _hand: A list of minions in the hand.
    #   - _board: A list of minions on the board.
    #   - _recruits: A list of current recruits.
    _turn_number: int
    _hero_health: int
    _tavern_tier: int
    _gold: int
    _hand: List[Optional[Minion]]
    _board: List[Optional[Minion]]
    _recruits: List[Optional[Minion]]

    def __init__(self, hero_health: int = 40, tavern_tier: int = 1) -> None:
        """Initialise the TavernGameBoard.

        Args:
            hero_health: The starting health of the hero.
            tavern_tier: The starting tier of the tavern.
        """
        self._turn_number = 0
        self._hero_health = hero_health
        self._tavern_tier = tavern_tier
        self._gold = 0

        self._hand = [None] * MAX_HAND_SIZE
        self._board = [None] * MAX_TAVERN_BOARD_SIZE
        self._recruits = [None] * MAX_TAVERN_RECRUIT_SIZE

    def next_turn(self) -> None:
        """Reset the tavern to the start of the next turn."""
        self._turn_number += 1
        self._gold = min(self._turn_number * GOLD_PER_TURN, MAX_TAVERN_GOLD)

    def upgrade_tavern(self) -> bool:
        """Upgrade the tavern. Return whether the upgrade was successful.

        >>> board = TavernGameBoard()
        >>> board.next_turn()
        >>> board.upgrade_tavern()  # Not enough gold (we only have 1)!
        False
        >>> board.tavern_tier == 1
        True
        >>> for _ in range(4): board.next_turn()
        >>> board.upgrade_tavern()  # We now have 5 gold
        True
        >>> board.tavern_tier == 2
        True
        >>> board.gold == 0
        True
        """
        if self._tavern_tier == MAX_TAVERN_TIER:
            # We can't upgrade since we already have the max tier!
            return False

        cost = TAVERN_UPGRADE_COSTS[self._tavern_tier]
        if not self._spend_gold(cost):
            # We can't upgrade since we don't have enough gold!
            return False

        self._tavern_tier += 1
        return True

    def attack_hero(self, damage: int) -> None:
        """Attack the tavern hero with the given amount of damage.

        >>> board = TavernGameBoard()  # Initialise board with 40 health!
        >>> board.attack_hero(10)
        >>> board.hero_health
        30
        """
        self._hero_health -= damage

    @property
    def is_dead(self) -> bool:
        """Return whether the hero is dead.

        >>> board = TavernGameBoard()  # Initialise board with 40 health!
        >>> board.attack_hero(31)
        >>> board.is_dead
        False
        >>> board.attack_hero(20)
        >>> board.is_dead
        True
        """
        return self._hero_health <= 0

    def _spend_gold(self, amount: int) -> bool:
        """Return whether the given amount of gold can be spent. If it can be,
        mutate the TavernGameBoard by subtracting that amount from the current gold total.

        >>> board = TavernGameBoard()
        >>> board._spend_gold(1)  # No turns have been started, so we have 0 gold!
        False
        >>> board.next_turn()  # We have 1 gold
        >>> board._spend_gold(100)
        False
        >>> board._spend_gold(1)
        True
        >>> board.gold == 0
        True
        """
        if self._gold < amount:
            return False

        self._gold -= amount
        return True

    @property
    def turn_number(self) -> int:
        """Return the current turn number."""
        return self._turn_number

    @property
    def hero_health(self) -> int:
        """Return the current health of the hero."""
        return self._hero_health

    @property
    def tavern_tier(self) -> int:
        """Return the current tier of the tavern."""
        return self._tavern_tier

    @property
    def gold(self) -> int:
        """Return the current gold that the player has."""
        return self._gold


class BattlegroundsGame:
    """A class representing the state of a Hearthstone Battlegrounds game.
    """
    # Private Instance Attributes
    #   - _num_players: The number of players at the start of the game.
    #   - _boards: The recruitment game board for each player.
    _num_players: int
    _boards: List[TavernGameBoard]

    def __init__(self, num_players: int = 8) -> None:
        """Initialise the BattlegroundsGame with the given number of players.
        Raise ValueError if num_players is negative or odd.

        Args:
            num_players: The number of players at the start of the game.
                         This MUST be an even positive integer.
        """
        # The number of players must be even!
        if num_players <= 0 or num_players % 2 == 1:
            raise ValueError(f'{num_players} is an invalid number of players!')

        self._num_players = num_players
        # Initialise an empty tavern for each player.
        self._boards = [TavernGameBoard() for _ in range(num_players)]


if __name__ == '__main__':
    import doctest
    doctest.testmod()