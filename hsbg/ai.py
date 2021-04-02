"""Framework for making Hearthstone Battlegrounds AI."""
import copy
import random
from typing import Tuple, List
from hsbg import BattlegroundsGame, Action, Move


class Player:
    """An abstract class representing a Hearthstone Battlegrounds AI.

    This class can be subclassed to implement different strategies for playing the game.
    """

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
        return random.choice(possible_moves)


def run_games(n: int, players: List[Player]) -> None:
    """Run n games using the given Players.

    Preconditions:
        - n >= 1
        - len(players) > 0 and len(players) % 2 == 0
    """
    stats = {i: 0 for i in range(len(players))}
    for i in range(0, n):
        players_copy = copy.deepcopy(players)
        winner, _ = run_game(players)
        stats[winner] += 1
        print(f'Game {i + 1} winner: Player {winner + 1}')

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')


def run_game(players: List[Player]) -> tuple[int, List[Tuple[int, Move]]]:
    """Run a Battlegrounds game between the given players.

    Return the index of the winning player and a list of moves made in the game,
    represented as tuples containing the index of the acting player and the move itself.

    Preconditions:
        - len(players) > 0 and len(players) % 2 == 0
    """
    game = BattlegroundsGame(num_players=len(players))
    move_sequence = []
    while game.winner is None:
        for index, player in enumerate(players):
            game.start_turn_for_player(index)
            while game.is_turn_in_progress:
                move = player.make_move(game)
                game.make_move(move)
                move_sequence.append((index, move))
        game.next_round()

    return game.winner, move_sequence