"""Framework for making Hearthstone Battlegrounds AI."""
from __future__ import annotations
import copy
import time
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Tuple, List, FrozenSet, Set, Dict, Callable, Optional
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


@dataclass(eq=True, frozen=True)
class _CompactGameState:
    """This is a simplified representation of the BattlegroundsGame for a single player.
    Note that minions are stored as a string representation.

    Instance Attributes:
        - tavern_tier: The tier of the tavern.
        - hero_health: The health of the hero.
        - gold: The amount of gold.
        - is_frozen: Whether the recruits are frozen.
        - hand: The minions in the hand.
        - board: The minions on the board.
        - recruits: The minions available for purchase.
    """
    tavern_tier: int
    hero_health: int
    gold: int
    is_frozen: bool
    hand: FrozenSet[str]
    board: FrozenSet[str]
    recruits: FrozenSet[str]
    round_number: int

    def from_game(game: BattlegroundsGame, player: int) -> _CompactGameState:
        """Return a game tree node for the given player in the given BattlegroundsGame.

        Preconditions:
            - 0 <= player < game.num_total_players
        """
        board = game.boards[player]
        return _CompactGameState(
            board.tavern_tier,
            board.hero_health,
            board.gold,
            board.is_frozen,
            frozenset({str(x) for x in board.get_minions_in_hand()}),
            frozenset({str(x) for x in board.get_minions_on_board()}),
            frozenset({str(x) for x in board.recruits if x is not None}),
            game.round_number
        )


@dataclass(eq=True, frozen=True, unsafe_hash=True)
class _GameTreeNode:
    """A node of the Monte Carlo game tree. This represents a transition between two states.

    Instance Attributes:
        - state: The current game state.
        - move: The move that resulted in this game state, or None if the start of a turn.
        - game: The BattlegroundsGame instance corresponding to this state.
    """
    state: _CompactGameState
    move: Optional[Move]
    game: BattlegroundsGame = field(compare=False, hash=False)


class MonteCarloTreeSearcher:
    """A Monte Carlo tree searcher for the BattlegroundsGame.

    Instance Attributes:
        - exploration_weight: The exploration parameter (c) in the upper confidence bound.
    """
    # Private Instance Attributes:
    #   - _total_rewards: A dict mapping the total reward of each game state.
    #   - _visit_counts: A dict mapping the total visit count for each game state.
    #   - _children: A dict mapping the children of each game state.
    #   - _friendly_player: The index of the friendly player.
    exploration_weight: float
    _total_rewards: Dict[_GameTreeNode, int]
    _visit_counts: Dict[_GameTreeNode, int]
    _children: Dict[_GameTreeNode, Set[_GameTreeNode]]
    _friendly_player: int

    def __init__(self, friendly_player: int, exploration_weight: float = 2**0.5):
        self.exploration_weight = exploration_weight
        self._total_rewards = defaultdict(int)
        self._visit_counts = defaultdict(int)
        self._children = dict()
        self._friendly_player = friendly_player

    def choose(self, game: BattlegroundsGame,
               metric: Optional[Callable[[BattlegroundsGame], float]] = None) -> _GameTreeNode:
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

        node = self._make_node_from_game(game)
        if node not in self._children:
            return self._get_random_successor(node)

        metric = metric or self._average_reward
        return max(self._children[node], key=metric)

    def _average_reward(self, node: _GameTreeNode) -> float:
        """Return the average reward of the given node.
        Return ``float(-inf)`` (negative infinity) if the node has not been visited.
        """
        if self._visit_counts[node] == 0:
            return float('-inf')
        else:
            return self._total_rewards[node] / self._visit_counts[node]

    def rollout(self, game: BattlegroundsGame) -> None:
        """Rollout the tree from the given game state."""
        node = self._make_node_from_game(game)
        path = self._select(node)
        leaf = path[-1]
        print(f'Expanding node {leaf}')
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node: _GameTreeNode) -> List[_GameTreeNode]:
        """Return a path to an unexplored descendent of the given node."""
        path = []
        while True:
            path.append(node)
            if node not in self._children or not self._children[node]:
                # The current node is either unexplored, or done.
                # In either case, we are done!
                return path
            # Get the remaining unexplored nodes
            unexplored = self._children[node] - self._children.keys()
            if unexplored:
                # Select any unexplored node, and we are done!
                path.append(unexplored.pop())
                return path
            else:
                # Select a node according to the upper confidence bound
                node = self._uct_select(node)

    def _expand(self, node: _GameTreeNode) -> None:
        """Expand the tree at the given node with the possible moves available."""
        if node in self._children:
            return
        else:
            self._children[node] = self._get_successors(node)

    def _simulate(self, node: _GameTreeNode) -> int:
        """Return the reward for a random simulation from the given node."""
        while True:
            if node.game.is_done:
                winning_player = node.game.winner
                assert winning_player is not None
                return int(winning_player == self._friendly_player)

            node = self._get_random_successor(node)

    def _backpropagate(self, path: List[_GameTreeNode], reward: int) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for node in reversed(path):
            print(f'Adding reward {reward}')
            self._total_rewards[node] += reward
            self._visit_counts[node] += 1

    def _uct_select(self, node: _GameTreeNode) -> _GameTreeNode:
        """Return a child of the given node which maximizes the upper confidence bound."""
        # All children of node should already be expanded
        assert all(x in self._children for x in self._children[node])

        log_visit_count = math.log(self._visit_counts[node])
        def _uct(n: _GameTreeNode) -> float:
            """Return the upper confidence bound for the given node."""
            exploration_coefficient = math.sqrt(log_visit_count / self._visit_counts[n])
            return self._average_reward(n) + self.exploration_weight * exploration_coefficient

        return max(self._children[node], key=_uct)

    def _get_successors(self, node: _GameTreeNode) -> Set[_GameTreeNode]:
        """Return all the possible successors from the given game."""
        return {
            self._get_successor(node, move)
            for move in node.game.get_valid_moves()
        }

    def _get_random_successor(self, node: _GameTreeNode) -> _GameTreeNode:
        """Return a random successor of the given game."""
        move = random.choice(node.game.get_valid_moves())
        return self._get_successor(node, move)

    def _get_successor(self, node: _GameTreeNode, move: Move) -> _GameTreeNode:
        """Return the succeeding game state after making the given move."""
        game_copy = node.game.copy_and_make_move(move)
        # Randomly simulate every other player, if the friendly player turn is done.
        if game_copy.has_completed_turn(self._friendly_player):
            for index in game_copy.alive_players:
                if game_copy.has_completed_turn(index):
                    continue
                game_copy.start_turn_for_player(index)
                while game_copy.is_turn_in_progress:
                    move = random.choice(game_copy.get_valid_moves())
                    game_copy.make_move(move)
            game_copy.next_round()
            game_copy.start_turn_for_player(self._friendly_player)

        n = self._make_node_from_game(game_copy)
        assert n.move == move
        return n

    def _make_node_from_game(self, game: BattlegroundsGame) -> _GameTreeNode:
        """Return the _GameTreeNode corresponding to the given game."""
        state = _CompactGameState.from_game(game, self._friendly_player)
        # Get the move that led to this state
        move_history = game._move_history[self._friendly_player]
        if move_history:
            move = move_history[-1]
        else:
            move = None
        return _GameTreeNode(state, move, game)


class MCTSPlayer(Player):
    """A Hearthstone Battlegrounds AI that uses a Monte Carlo tree searcher to pick moves."""
    # Private Instance Attributes
    #   - _mcts: The Montre Carlo tree searcher.
    #   - _iterations: The number of rollouts to perform before making a move.
    #   - _warmup_iterations: The number of rollouts to perform before making a move.
    _mcts: MonteCarloTreeSearcher
    _iterations: int
    _warmup_iterations: int

    def __init__(self, index: int, exploration_weight: float = 2**0.5, iterations: int = 50,
                 warmup_iterations: int = 0):
        """Initialise this MCTSPlayer.

        Preconditions:
            - iterations >= 0
            - warmup_iterations >= 0

        Args:
            index: The index of this player.
            exploration_weight: Exploration weight in the UCT bound.
            iterations: The number of rollouts to perform before making a move.
            warmup_iterations: The number of rollouts to perform when initialising the tree.
        """
        self._mcts = MonteCarloTreeSearcher(index, exploration_weight=exploration_weight)
        self._iterations = iterations
        self._warmup_iterations = warmup_iterations

    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        # if game._previous_move is None:
        #     self._train(game, self._warmup_iterations)
        self._train(game, self._iterations)
        node = self._mcts.choose(game)
        return node.move

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