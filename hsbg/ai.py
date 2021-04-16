"""Framework for making Hearthstone Battlegrounds AI."""
import copy
import random
from typing import Tuple, List, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from hsbg import BattlegroundsGame, Move
from hsbg.mcts import MonteCarloTreeSearcher


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


class MCTSPlayer(Player):
    """A Hearthstone Battlegrounds AI that uses a Monte Carlo tree searcher to pick moves."""
    # Private Instance Attributes
    #   - _mcts: The Montre Carlo tree searcher.
    #   - _iterations: The number of rollouts to perform before making a move.
    #   - _warmup_iterations: The number of rollouts to perform before making a move.
    def __init__(self, exploration_weight: float = 2**0.5, iterations: int = 50,
                 warmup_iterations: int = 0):
        """Initialise this MCTSPlayer.

        Preconditions:
            - iterations >= 0
            - warmup_iterations >= 0

        Args:
            exploration_weight: Exploration weight in the UCT bound.
            iterations: The number of rollouts to perform before making a move.
            warmup_iterations: The number of rollouts to perform when initialising the tree.
        """
        self._mcts = MonteCarloTreeSearcher(exploration_weight=exploration_weight)
        self._iterations = iterations
        self._warmup_iterations = warmup_iterations

    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        if game._previous_move is None:
            self._train(game, self._warmup_iterations)
        self._train(game, self._iterations)
        next_game = self._mcts.choose(game)
        return next_game._previous_move[1]

    def _train(self, game: BattlegroundsGame, n_iterations: int) -> None:
        """Train the Monte Carlo tree searcher by performing the given amount of rollouts
        from the given game state.
        """
        for _ in range(n_iterations):
            self._mcts.rollout(game)


def run_games(n: int, players: List[Player], n_jobs: int = 1, use_thread_pool: bool = False) \
        -> None:
    """Run n games using the given Players.

    Args:
        n: The number of games to run.
        players: A list of players to run the games with.
        n_jobs: The number of games to run in parallel.
        use_threadpool: Whether to use the thread pool or process pool executor.

                        Note that when using a process pool executor, this function
                        must be guarded by ``if __name__ == '__main__':``.

    Preconditions:
        - n >= 1
        - len(players) > 0 and len(players) % 2 == 0
        - n_jobs >= 1
    """
    stats = {i: 0 for i in range(len(players))}

    Executor = ThreadPoolExecutor if use_thread_pool else ProcessPoolExecutor
    with Executor(max_workers=n_jobs) as pool:
        futures = [pool.submit(run_game, copy.deepcopy(players)) for _ in range(n)]
        for game_index, future in enumerate(as_completed(futures)):
            winner, _ = future.result()
            stats[winner] += 1
            print(f'Game {game_index + 1} winner: Player {winner + 1}')

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')


def run_game(players: List[Player]) -> Tuple[int, List[Tuple[int, Move]]]:
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