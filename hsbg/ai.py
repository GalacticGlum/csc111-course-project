"""Framework for making Hearthstone Battlegrounds AI."""
from __future__ import annotations
import copy
import time
import math
import random
from dataclasses import dataclass
from collections import defaultdict
from typing import Tuple, List, Set, Dict, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from hsbg import BattlegroundsGame, Move


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


@dataclass
class GameTreeNode:
    """A node of the Monte Carlo game tree.

    This is a simplified representation of the BattlegroundsGame for a single player.
    Note that minions are stored as a string representation.

    Instance Attributes:
        - tavern_tier: The tier of the tavern.
        - hero_health: The health of the hero.
        - gold: The amount of gold.
        - is_frozen: Whether the recruits are frozen.
        - hand: The minions in the hand.
        - board: The minions on the board.
        - recruits: The minions available for purchase.
        - move: The move that resulted in this game state, or None if the start of a turn.
    """
    tavern_tier: int
    hero_health: int
    gold: int
    is_frozen: bool
    hand: Set[str]
    board: Set[str]
    recruits: Set[str]
    round_number: int


    def from_game(game: BattlegroundsGame, player: int) -> GameTreeNode:
        """Return a game tree node for the given player in the given BattlegroundsGame.

        Preconditions:
            - 0 <= player < game.num_total_players
        """
        board = game.board[player]
        return GameTreeNode(
            board.tavern_tier,
            board.hero_health,
            board.gold,
            board.is_frozen,
            {str(x) for x in board.get_minions_in_hand()},
            {str(x) for x in board.get_minions_on_board()},
            {str(x) for x in board.recruits if x is not None},
            board.round_number
        )


class MonteCarloTreeSearcher:
    """A Monte Carlo tree searcher for the BattlegroundsGame.

    Instance Attributes:
        - exploration_weight: The exploration parameter (c) in the upper confidence bound.
    """
    # Private Instance Attributes:
    #   - _total_rewards: A dict mapping the total reward of each game state.
    #   - _visit_counts: A dict mapping the total visit count for each game state.
    #   - _children: A dict mapping the children of each game state.
    exploration_weight: float
    _total_rewards: Dict[GameTreeNode, int]
    _visit_counts: Dict[GameTreeNode, int]
    _children: Dict[GameTreeNode, Set[GameTreeNode]]

    def __init__(self, exploration_weight: float = 2**0.5):
        self.exploration_weight = exploration_weight
        self._total_rewards = defaultdict(int)
        self._visit_counts = defaultdict(int)
        self._children = dict()

    def choose(self, game: BattlegroundsGame,
               metric: Optional[Callable[[BattlegroundsGame], float]] = None) -> BattlegroundsGame:
        """Return the best successor of the given game state according to the given metric function
        That is, find a child of the given game state which maximizes the given metric.

        Raise a ValueError if the given game state is done (terminal).

        Args:
            game: The game state whose children to select from.
            metric: A function which takes in a game state as input and returns a numerical score
                    measuring the fitness (i.e. the 'goodness') of the game state. Defaults to the
                    average reward of the game state.
        """
        if game.is_done:
            raise ValueError(f'choose called on a game state that is done {game}')

        if game not in self._children:
            return MonteCarloTreeSearcher._get_random_successor(game)

        metric = metric or self._average_reward
        return max(self._children[game], key=metric)

    def _average_reward(self, game: BattlegroundsGame) -> float:
        """Return the average reward of the given game state.
        Return ``float(-inf)`` (negative infinity) if the game state has not been visited.
        """
        if self._visit_counts[game] == 0:
            return float('-inf')
        else:
            return self._total_rewards[game] / self._visit_counts[game]

    def rollout(self, game: BattlegroundsGame) -> None:
        """Rollout the tree from the given game state."""
        path = self._select(game)
        leaf = path[-1]
        self._expand(leaf)
        winning_player = self._simulate(leaf)
        self._backpropagate(path, winning_player)

    def _select(self, game: BattlegroundsGame) -> List[BattlegroundsGame]:
        """Return a path to an unexplored descendent of the given game state."""
        path = []
        while True:
            path.append(game)
            if game not in self._children or not self._children[game]:
                # The current game state is either unexplored, or done.
                # In either case, we are done!
                return path
            # Get the remaining unexplored game states
            unexplored = self._children[game] - self._children.keys()
            if unexplored:
                # Select any unexplored game state, and we are done!
                path.append(unexplored.pop())
                return path
            else:
                # Select a game state according to the upper confidence bound
                game = self._uct_select(game)

    def _expand(self, game: BattlegroundsGame) -> None:
        """Expand the tree at the given game state with the possible moves available."""
        if game in self._children:
            return
        else:
            self._children[game] = MonteCarloTreeSearcher._get_successors(game)

    def _simulate(self, game: BattlegroundsGame) -> int:
        """Return the winner for a random simulation from the given game state."""
        while True:
            if game.is_done:
                winning_player = game.winner
                assert winning_player is not None
                return winning_player

            game = MonteCarloTreeSearcher._get_random_successor(game)

    def _backpropagate(self, path: List[BattlegroundsGame], winning_player: int) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for game in reversed(path):
            # Add reward, making sure to invert if this game represents the enemy player
            reward = int(winning_player == game.active_player)
            print(f'Adding reward {reward} (active_player={game.active_player})')
            self._total_rewards[game] += reward
            self._visit_counts[game] += 1

    def _uct_select(self, game: BattlegroundsGame) -> BattlegroundsGame:
        """Return a child of the given game which maximizes the upper confidence bound."""
        # All children of game should already be expanded
        assert all(x in self._children for x in self._children[game])

        log_visit_count = math.log(self._visit_counts[game])
        def _uct(n: BattlegroundsGame) -> float:
            """Return the upper confidence bound for the given game."""
            exploration_coefficient = math.sqrt(log_visit_count / self._visit_counts[n])
            return self._average_reward(n) + self.exploration_weight * exploration_coefficient

        return max(self._children[game], key=_uct)

    @staticmethod
    def _get_successors(game: BattlegroundsGame) -> Set[BattlegroundsGame]:
        """Return all the possible successors from the given game."""
        return {
            MonteCarloTreeSearcher._get_successor(game, move)
            for move in game.get_valid_moves()
        }

    @staticmethod
    def _get_random_successor(game: BattlegroundsGame) -> BattlegroundsGame:
        """Return a random successor of the given game."""
        move = random.choice(game.get_valid_moves())
        return MonteCarloTreeSearcher._get_successor(game, move)

    @staticmethod
    def _get_successor(game: BattlegroundsGame, move: Move) -> GameTreeNode:
        """Return the succeeding game state after making the given move."""
        game_copy = game.copy_and_make_move(move)
        # Do matchup if all the turns are completed
        if all(game_copy.has_completed_turn(i) for i in game_copy.alive_players):
            game_copy.next_round()

        if not game_copy.is_done and not game_copy.is_turn_in_progress:
            # Start the turn for the next player
            next_player = next(i for i in game_copy.alive_players if not game_copy.has_completed_turn(i))
            game_copy.start_turn_for_player(next_player)

        return game_copy


class MCTSPlayer(Player):
    """A Hearthstone Battlegrounds AI that uses a Monte Carlo tree searcher to pick moves."""
    # Private Instance Attributes
    #   - _mcts: The Montre Carlo tree searcher.
    #   - _iterations: The number of rollouts to perform before making a move.
    #   - _warmup_iterations: The number of rollouts to perform before making a move.
    _mcts: MonteCarloTreeSearcher
    _iterations: int
    _warmup_iterations: int

    def __init__(self, exploration_weight: float = 2**0.5, iterations: int = 1,
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
        move = next_game._previous_move[1]
        print(move)
        return move

    def _train(self, game: BattlegroundsGame, n_iterations: int) -> None:
        """Train the Monte Carlo tree searcher by performing the given amount of rollouts
        from the given game state.
        """
        if n_iterations == 0:
            return

        start_time = time.time()
        print(f'Training MCTS for {n_iterations} iterations')
        for _ in range(n_iterations):
            self._mcts.rollout(game)
        elapsed_time = time.time() - start_time
        print('Finished rollout in {:.2f} seconds ({:.2f} seconds per rollout)'.format(
            elapsed_time, elapsed_time / n_iterations
        ))


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