"""Implementation of various Hearthstone Battlegrounds players."""
import random
from abc import ABC, abstractmethod

from hsbg import BattlegroundsGame, Move


class Player(ABC):
    """An abstract class representing a Hearthstone Battlegrounds AI.

    This class can be subclassed to implement different strategies for playing the game.
    """

    @abstractmethod
    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        raise NotImplementedError


class RandomPlayer(Player):
    """A Hearthstone Battlegrounds AI whose strategy is always picking a random move."""

    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        possible_moves = game.get_valid_moves()
        move = random.choice(possible_moves)
        return move


class GreedyPlayer(Player):
    """A Hearthstone Battlegrounds AI that greedily chooses the move that maximizes average reward.
    """
    # Private Instance Attributes
    #   - _player_index: The index of this player.
    #   - _games_per_move: The number of games to simulate per move.
    _player_index: int
    _games_per_move: int

    def __init__(self, index: int, games_per_move: int = 10) -> None:
        """Initialise this GreedyPlayer.

        Preconditions:
            - games_per_move >= 0

        Args:
            index: The index of this player.
            games_per_move: The number of games to simulate per move.
        """
        self._player_index = index
        self._games_per_move = games_per_move

    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        moves = game.get_valid_moves()

        best_move_yet = None
        best_reward = float('-inf')
        for move in moves:
            total_reward = 0
            for _ in range(self._games_per_move):
                game_copy = game.copy_and_make_move(move)
                total_reward += self._simulate(game_copy)

            average_reward = total_reward / self._games_per_move
            if average_reward > best_reward:
                best_reward = average_reward
                best_move_yet = move

        return best_move_yet

    def _simulate(self, game: BattlegroundsGame) -> int:
        """Return the reward for a random simulation from the given game.
        Every player moves randomly.
        """
        game.clear_turn_completion()
        while game.winner is None:
            for index in game.alive_players:
                game.start_turn_for_player(index)
                while game.is_turn_in_progress:
                    move = random.choice(game.get_valid_moves())
                    game.make_move(move)
            game.next_round()

        # A reward of 1 if we win, and 0 if we lose.
        reward = int(game.winner == self._player_index)
        return reward
