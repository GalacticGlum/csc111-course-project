"""A simulator for Hearthstone Battlegrounds."""
from typing import List, Optional

from hsbg.minions import Minion, MinionPool

# The maximum number of minions a player can have in their hand.
MAX_HAND_SIZE = 10
# The maximum number of minions that can be on the board in a tavern.
MAX_TAVERN_BOARD_SIZE = 7
# The number of recruits to offer the player at the start of the game.
INITIAL_NUM_RECRUITS = 3
# A list mapping each tavern tier to the additional number of recruits gained at that tier.
# The element at index i indicates the additional recruits gained after upgrading FROM tier i.
RECRUIT_NUM_PROGRESSION = [
    0,  # Padding element
    1,  # One new recruit after upgrading from tier 1
    0,  # No new recruit after upgrading from tier 2
    1,  # One new recruit after upgrading from tier 3
    0,  # No onew recruit after upgrading from tier 4
    1  # One new recruit after upgrading from tier 5
]
# The amount of gold a refresh costs.
TAVERN_REFRESH_COST = 1
# The maximum number of recruits that can be on the board in a tavern.
MAX_TAVERN_RECRUIT_SIZE = 6
# The maximum number of gold the player can have.
MAX_TAVERN_GOLD = 10
# The amount of gold the player gets per turn.
GOLD_PER_TURN = 1

# A list mapping each tavern tier to its upgrade cost.
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


class TurnClock:
    """A mechanism for calling a function after a given amount of turns.

    Instance Attributes:
        duration: The number of turns until the clock is complete.

    >>> clock = TurnClock(2)
    >>> clock.step()  # Turn 1
    False
    >>> clock.step()  # Turn 2
    True
    """
    # Private Instance Attributes:
    #   - _remaining: The number of turns remaining.
    #   - _on_complete: A function called when the clock is complete.

    def __init__(self, duration: int, on_complete: Optional[callable] = None) -> None:
        """Initialise the TurnClock with a duration.

        Args:
            duration: The number of turns until the clock is complete.
            on_complete: A function to call when the clock is complete.
                         This is called on the turn that the clock is complete.
        """
        self.duration = duration
        self._on_complete = on_complete
        self.reset()

    def step(self, n: int = 1) -> bool:
        """Step the clock by the given number of turns. Return whether the clock is complete."""
        if self.done:
            return True

        self._remaining -= n
        done = self.done
        if done and self._on_complete is not None:
            self._on_complete()

        return done

    def reset(self) -> None:
        """Reset the clock."""
        self._remaining = self.duration

    @property
    def done(self) -> bool:
        """Return whether the clock is complete."""
        return self._remaining <= 0


class TavernGameBoard:
    """A class representing the state of a tavern game board for a single player."""
    # Private Instance Attributes:
    #   - _turn_number: The current turn (where 1 indicates the first turn).
    #   - _hero_health: The current health of the hero.
    #   - _tavern_tier: The current tier of the tavern.
    #   - _gold: The current gold that the player has.
    #   - _hand: A list of minions in the hand.
    #   - _board: A list of minions on the board.
    #   - _pool: The pool of minions to select recruits from.
    #   - _num_recruits: The number of recruits offered to the player currently.
    #   - _recruits: A list of current recruits.
    #   - _is_frozen: Whether the recruit selection is currently frozen.
    #   - _refresh_cost: The current cost of refreshing the recruitment pool.
    #   - _refresh_cost_clock: Clock to manage when to change the refresh cost.
    _turn_number: int
    _hero_health: int
    _tavern_tier: int
    _gold: int
    _hand: List[Optional[Minion]]
    _board: List[Optional[Minion]]
    _pool: MinionPool

    _num_recruits: int
    _recruits: List[Optional[Minion]]
    _is_frozen: bool

    _refresh_cost: int
    _refresh_cost_clock: Optional[TurnClock]

    def __init__(self, pool: Optional[MinionPool] = None, hero_health: int = 40, tavern_tier: int = 1) \
            -> None:
        """Initialise the TavernGameBoard.

        Args:
            pool: The pool of minions to select recruits from.
            hero_health: The starting health of the hero.
            tavern_tier: The starting tier of the tavern.
        """
        self._turn_number = 0
        self._hero_health = hero_health
        self._tavern_tier = tavern_tier
        self._gold = 0

        self._hand = [None] * MAX_HAND_SIZE
        self._board = [None] * MAX_TAVERN_BOARD_SIZE
        self._pool = pool or MinionPool()

        self._num_recruits = INITIAL_NUM_RECRUITS
        self._recruits = [None] * MAX_TAVERN_RECRUIT_SIZE
        self._is_frozen = False

        self._refresh_cost = TAVERN_REFRESH_COST
        self._refresh_cost_clock = None

    def next_turn(self) -> None:
        """Reset the tavern to the start of the next turn.

        >>> board = TavernGameBoard()
        >>> board.next_turn()
        >>> board.turn_number == 1
        True
        >>> board._spend_gold(1)
        True
        >>> board.gold == 0
        True
        >>> board.next_turn()
        >>> board.turn_number == 2
        True
        >>> board.gold == 2
        True
        """
        self._turn_number += 1
        self._gold = min(self._turn_number * GOLD_PER_TURN, MAX_TAVERN_GOLD)
        self._refresh_recruits()
        if self._is_frozen:
            self._is_frozen = False

        # Update refresh cost
        if self._refresh_cost_clock is not None:
            self._refresh_cost_clock.step()

    def _refresh_recruits(self) -> bool:
        """Refresh the selection of recruits without spending gold.
        Do nothing if the selection is frozen. Return whether the recruits were refreshed.
        """
        if self._is_frozen:
            return False

        # Insert non-None minions back into the pool.
        self._pool.insert([minion for minion in self._recruits if minion is not None])
        # Roll new minions from pool
        minions = self._pool.get_random(n=self._num_recruits, max_tier=self._tavern_tier)
        # Fill recruit list from left to right
        for i, minion in enumerate(minions):
            self._recruits[i] = minion
        return True

    def refresh_recruits(self) -> bool:
        """Refresh the selection of recruits. Do nothing if the selection is frozen,
        or if the player does not have enough gold. Return whether the recruits were refreshed.

        >>> board = TavernGameBoard()
        >>> board.refresh_recruits()  # No turns have been started, so we have 0 gold!
        False
        >>> board.next_turn()
        >>> board.refresh_recruits()
        True
        >>> board.gold == 0
        True
        >>> board.next_turn()
        >>> board.freeze()
        >>> board.refresh_recruits()
        False
        """
        if not self._can_spend_gold(self._refresh_cost):
            # We can't refresh since we don't have enough gold!
            return False
        if not self._refresh_recruits():
            # The refresh was not successful!
            return False

        # The refresh was successful so subtract the amount from the gold total.
        self._spend_gold(self._refresh_cost)
        return True

    def set_refresh_cost(self, amount: int, turns: Optional[int] = 1) -> None:
        """Set the recruit refresh cost.

        Args:
            amount: The new cost of refreshing the recruitment pool.
            turns: The amount of turns to keep this cost.
                   If None, then the new refresh cost is indefinite.

        >>> board = TavernGameBoard()
        >>> board.set_refresh_cost(100, turns=1)
        >>> board.refresh_cost
        100
        >>> board.next_turn()
        >>> board.refresh_cost
        100
        >>> board.next_turn()
        >>> board.refresh_cost
        1
        """
        self._refresh_cost = amount
        if turns is not None:
            self._refresh_cost_clock = TurnClock(turns + 1, on_complete=self._reset_refresh_cost)

    def _reset_refresh_cost(self) -> None:
        """Reset the refresh cost to the default value. This also clears the refresh cost clock."""
        self._refresh_cost = TAVERN_REFRESH_COST
        self._refresh_cost_clock = None

    def upgrade_tavern(self) -> bool:
        """Upgrade the tavern. Do nothing if the tavern cannot be upgraded anymore,
        or if the player does not have enough gold. Return whether the upgrade was successful.

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
        self._num_recruits += RECRUIT_NUM_PROGRESSION[self._tavern_tier]
        return True

    def freeze(self) -> None:
        """Freeze the selection of recruit minions.

        >>> board = TavernGameBoard()
        >>> board.next_turn()

        >>> previous_recruits = list(board._recruits)
        >>> board.next_turn()
        >>> previous_recruits == board._recruits
        False

        >>> board.freeze()
        >>> board.is_frozen
        True

        >>> previous_recruits = list(board._recruits)
        >>> board.next_turn()
        >>> previous_recruits == board._recruits
        True
        """
        self._is_frozen = True

    def unfreeze(self) -> None:
        """Unfreeze the selection of recruit minions.

        >>> board = TavernGameBoard()
        >>> board.freeze()
        >>> board.unfreeze()
        >>> board.is_frozen
        False
        """
        self._is_frozen = False

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

    def _can_spend_gold(self, amount: int) -> bool:
        """Return whether the given amount of gold can be spent.

        >>> board = TavernGameBoard()
        >>> board._can_spend_gold(1)  # No turns have been started, so we have 0 gold!
        False
        >>> board.next_turn()  # We have 1 gold
        >>> board._can_spend_gold(100)
        False
        >>> board._can_spend_gold(1)
        True
        """
        return self._gold >= amount

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
        if not self._can_spend_gold(amount):
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

    @property
    def is_frozen(self) -> bool:
        """Return whether the recruit selection is currently frozen."""
        return self._is_frozen

    @property
    def refresh_cost(self) -> int:
        """Return the current cost of refreshing the recruitment pool."""
        return self._refresh_cost


class BattlegroundsGame:
    """A class representing the state of a Hearthstone Battlegrounds game."""
    # Private Instance Attributes
    #   - _num_players: The number of players at the start of the game.
    #   - _boards: The recruitment game board for each player.
    #   - _pool: The pool of minions shared across all players.
    _num_players: int
    _boards: List[TavernGameBoard]
    _pool: MinionPool

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
        self._pool = MinionPool()
        self._boards = [TavernGameBoard(pool=self._pool) for _ in range(num_players)]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
