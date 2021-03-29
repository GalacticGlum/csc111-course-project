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
TAVERN_GOLD_PER_TURN = 1


class TavernGameBoard:
    """A class representing the state of a tavern game board for a single player."""
    # Private Instance Attributes:
    #   - _hero_health: The current health of the hero.
    #   - _tavern_tier: The current tier of the tavern.
    #   - _gold: The current gold that the player has.
    #   - _hand: A list of minions in the hand.
    #   - _board: A list of minions on the board.
    #   - _recruits: A list of current recruits.
    _hero_health: int
    _tavern_tier: int
    _gold: int
    _hand: List[Optional[Minion]]
    _board: List[Optional[Minion]]
    _recruits: List[Optional[Minion]]

    def __init__(self, hero_health: int = 40, tavern_tier: int = 1) -> None:
        """Initialize the TavernGameBoard.

        Args:
            hero_health: The starting health of the hero.
            tavern_tier: The starting tier of the tavern.
        """
        self._hero_health = hero_health
        self._tavern_tier = tavern_tier
        self._gold = 0

        self._hand = [None] * MAX_HAND_SIZE
        self._board = [None] * MAX_TAVERN_BOARD_SIZE
        self._recruits = [NONE] * MAX_TAVERN_RECRUIT_SIZE


class BattlegroundsGame:
    """A class representing the state of a Hearthstone Battlegrounds game.
    """
    # Private Instance Attributes
    #   - _num_players: The number of players at the start of the game.
    #   - _boards: The recruitment game board for each player.
    _num_players: int
    _boards: List[TavernGameBoard]

    def __init__(self, num_players: int = 8) -> None:
        """Initialize the BattlegroundsGame with the given number of players.
        Raise ValueError if num_players is negative or odd.

        Args:
            num_players: The number of players at the start of the game.
                         This MUST be an even positive integer.
        """
        # The number of players must be even!
        if num_players <= 0 or num_players % 2 == 1:
            raise ValueError(f'{num_players} is an invalid number of players!')

        self._num_players = num_players
        # Initialize an empty tavern for each player.
        self._boards = [TavernGameBoard() for _ in range(num_players)]