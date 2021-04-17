"""Framework for making Hearthstone Battlegrounds AI.
This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
from __future__ import annotations
import json
import copy
import time
import math
import random
from queue import Queue
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, List, FrozenSet, Set, Callable, Optional, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import dill as pickle
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from hsbg.utils import get_seed
from hsbg import BattlegroundsGame, TavernGameBoard, Move, Action
from hsbg.visualisation import init_display, flip_display, close_display, draw_game


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
class _DeterministicTavernGameBoard:
    """This is a simplified and deterministic representation of the TavernGameBoard.
    Note that minions are stored as a string representation.

    Instance Attributes:
        - tavern_tier: The tier of the tavern.
        - gold: The amount of gold available.
        - is_frozen: Whether the recruits are frozen.
        - hand: The minions in the hand.
        - board: The minions on the board.
        - recruits: The minions available for purchase.
    """
    tavern_tier: int
    gold: int
    is_frozen: bool
    hand: FrozenSet[str]
    board: FrozenSet[str]
    recruits: FrozenSet[str]

    @staticmethod
    def from_board(board: TavernGameBoard) -> _DeterministicTavernGameBoard:
        """Return a game tree node for the given TavernGameBoard."""
        return _DeterministicTavernGameBoard(
            board.tavern_tier,
            board.gold,
            board.is_frozen,
            frozenset({str(x) for x in board.get_minions_in_hand()}),
            frozenset({str(x) for x in board.get_minions_on_board()}),
            frozenset({str(x) for x in board.recruits if x is not None}),
        )


class _GameTree:
    """A node of the Monte Carlo game tree. This represents a transition between two states.

    Instance Attributes:
        - board: The game state corresponding to this tree.
        - move: The current move, or None if this tree represents the start of a game.
        - visit_count: The total number of times this tree has been visited.
        - total_reward: The total reward of this tree.
    """
    board: TavernGameBoard
    move: Optional[Move]
    visit_count: int
    total_reward: int
    # Private Instance Attributes:
    #  - _subtrees:
    #      the subtrees of this tree, which represent the game trees after a possible
    #      move by the current player
    #   - _seed: The seed used.
    _subtrees: List[_GameTree]
    _seed: Optional[int]
    _deterministic_state: _DeterministicTavernGameBoard

    def __init__(self, board: Optional[TavernGameBoard] = None, move: Optional[Move] = None,
                 seed: int = None) -> None:
        """Initialize a new game tree."""
        random.seed(seed)
        self.board = board or TavernGameBoard()
        if board is None:
            self.board.next_turn()

        self.move = move
        self.visit_count = 0
        self.total_reward = 0
        self._subtrees = []
        self._seed = seed
        self._deterministic_state = _DeterministicTavernGameBoard.from_board(self.board)

    def get_subtrees(self) -> List[_GameTree]:
        """Return the subtrees of this game tree."""
        return self._subtrees

    def find_subtree_by_move(self, move: Move) -> Optional[_GameTree]:
        """Return the subtree corresponding to the given move.

        Return None if no subtree corresponds to that move.
        """
        for subtree in self._subtrees:
            if subtree.move == move:
                return subtree

        return None

    def add_subtree(self, subtree: _GameTree) -> None:
        """Add a subtree to this game tree."""
        self._subtrees.append(subtree)

    @property
    def average_reward(self) -> float:
        """Return the average reward of this tree.
        Return ``float(-inf)`` (negative infinity) if the tree has not been visited.
        """
        if self.visit_count == 0:
            return float('-inf')
        else:
            return self.total_reward / self.visit_count

    def get_uct(self, exploration_weight: float = 2**0.5) -> float:
        """Return the upper confidence bound for this tree."""
        if self.visit_count == 0:
            return 0
        else:
            exploration_coefficient = math.sqrt(math.log(self.visit_count) / self.visit_count)
            return self.average_reward + exploration_weight * exploration_coefficient

    def uct_select(self) -> _GameTree:
        """Return a subtree of this tree which maximizes the upper confidence bound."""
        # All subtrees should already be expanded
        assert all(x.expanded for x in self._subtrees)
        return max(self._subtrees, key=lambda x: x.get_uct())

    def expand(self) -> None:
        """Expand this tree with the possible moves available."""
        if self.expanded or self.board.is_dead:
            return
        else:
            for subtree in self.get_possible_subtrees():
                self.add_subtree(subtree)

    @property
    def expanded(self) -> bool:
        """Return whether this tree has been expanded."""
        return len(self._subtrees) > 0

    def select(self) -> List[_GameTree]:
        """Return a path to an unexplored descendent of this tree."""
        path = []
        tree = self
        # TODO: this is probably the infinite loop error
        while True:
            path.append(tree)
            if tree.get_subtrees() == []:
                # We've reached a leaf node, so we are done.
                return path
            unexplored = [subtree for subtree in tree.get_subtrees() if not subtree.expanded]
            if unexplored:
                # Select any uunexplored child, and we are done!
                path.append(unexplored.pop())
                return path
            else:
                # Select a node according to the upper confidence bound.
                tree = tree.uct_select()

    def get_possible_subtrees(self) -> Set[_GameTree]:
        """Return all the possible subtrees from this tree."""
        moves = self.board.get_valid_moves() + [Move(Action.END_TURN)]
        return {self._make_subtree_from_move(move) for move in moves}

    def get_random_possible_subtree(self) -> _GameTree:
        """Return a random subtree of this tree."""
        move = random.choice(self.board.get_valid_moves() + [Move(Action.END_TURN)])
        return self._make_subtree_from_move(move)

    def _make_subtree_from_move(self, move: Move) -> _GameTree:
        """Return the subtree representing this tree after making the given move."""
        board_copy = copy.deepcopy(self.board)
        if move.action == Action.END_TURN:
            board_copy.next_turn()
        else:
            random.seed(self._seed)
            board_copy.make_move(move)
        return _GameTree(board_copy, move, seed=self._seed)

    def __str__(self) -> str:
        """Return a string representation of this tree."""
        return self._str_indented(0)

    def _str_indented(self, depth: int) -> str:
        """Return an indented string representation of this tree.

        The indentation level is specified by the <depth> parameter.
        """
        expanded = ', expanded' if self.expanded else ''
        stats = f'({self.total_reward}/{self.visit_count}) (seed={self._seed})'
        move_desc = f'{self._move_str()} {stats}{expanded} -> '
        s = '    ' * depth + move_desc

        offset = len(s)
        board_str = '\n'.join(
            (offset if index > 0 else 0) * ' ' + line
            for index, line in enumerate(self.board.as_format_str().splitlines())
        )
        s += board_str + '\n'
        if self._subtrees == []:
            return s
        else:
            for subtree in self._subtrees:
                s += subtree._str_indented(depth + 1)
            return s

    def _move_str(self) -> str:
        """Return a string representation of the move for this tree."""
        if self.move is None:
            return str(None)
        else:
            return f'({self.move.action.name}, index={self.move.index})'

    @property
    def seed(self) -> Optional[int]:
        """Return the seed of the GameTree."""
        return self._seed


class MonteCarloTreeSearcher:
    """A Monte Carlo tree searcher for the BattlegroundsGame.

    Instance Attributes:
        - exploration_weight: The exploration parameter (c) in the upper confidence bound.
    """
    # Private Instance Attributes:
    #   - _game_tree: The root of the game tree.
    #   - _friendly_player: The index of the friendly player.
    exploration_weight: float
    _game_tree: _GameTree
    _friendly_player: int

    def __init__(self, friendly_player: int, exploration_weight: float = 2**0.5, seed: int = None) \
            -> None:
        """Initialise a new MonteCarloTreeSearcher."""
        self.exploration_weight = exploration_weight
        self._game_tree = _GameTree(seed=seed)
        self._friendly_player = friendly_player

    def choose(self, game: BattlegroundsGame,
               metric: Optional[Callable[[_GameTree], float]] = None) -> _GameTree:
        """Return the best subtree of the given node according to the given metric function
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

        # Get the tree corresponding to the game board of the friendly player
        tree = self.get_tree_from_board(game.boards[self._friendly_player])
        if tree is None:
            raise ValueError('the given board state is not a node of the tree')

        if not tree.expanded:
            return tree.get_random_possible_subtree()

        def _average_reward_metric(x: _GameTree) -> float:
            """Return the average reward of the given tree."""
            return x.average_reward

        metric = metric or _average_reward_metric
        return max(tree.get_subtrees(), key=metric)

    def rollout(self, game: BattlegroundsGame) -> None:
        """Rollout the tree from the given game state."""
        if game.is_done:
            raise ValueError(f'rollout called on a game state that is done {game}')

        tree = self.get_tree_from_board(game.boards[self._friendly_player])
        if tree is None:
            print('rollout was given a game state that is not a node of the tree')
            return

        path = tree.select()
        leaf = path[-1]
        leaf.expand()
        reward = self._simulate(copy.deepcopy(game), path)
        MonteCarloTreeSearcher._backpropagate(path, reward)

    def _simulate(self, game: BattlegroundsGame, path: Optional[List[_GameTree]] = None) -> int:
        """Return the reward for a random simulation of the given game until completion.

        Args:
            game: The game to simulate from.
            path: A path of nodes for the friendly player to apply before assuming a random policy.
        """
        game.clear_turn_completion()
        current_node_index = 0

        while game.winner is None:
            for index in game.alive_players:
                game.start_turn_for_player(index)
                while game.is_turn_in_progress:
                    move = None
                    # If we are the friendly player, and we have nodes left, use the next element
                    # from the list of nodes (the path).
                    has_node_left = path is not None and current_node_index < len(path)
                    if game.active_player == self._friendly_player and has_node_left:
                        move = path[current_node_index].move
                        # Apply the seed for that node
                        random.seed(path[current_node_index].seed)
                        current_node_index += 1
                    # Otherwise, play randomly.
                    if move is None:
                        move = random.choice(game.get_valid_moves())
                    game.make_move(move)
            game.next_round()

        # A reward of 1 if we win, and 0 if we lose.
        reward = int(game.winner == self._friendly_player)
        return reward

    @staticmethod
    def _backpropagate(path: List[_GameTree], reward: int) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for tree in reversed(path):
            tree.total_reward += reward
            tree.visit_count += 1

    def get_tree_from_board(self, board: TavernGameBoard) -> Optional[_GameTree]:
        """Return the game tree corresponding to the given board."""
        q = Queue()
        q.put(self._game_tree)
        state = _DeterministicTavernGameBoard.from_board(board)
        while not q.empty():
            tree = q.get()
            if tree._deterministic_state == state:
                return tree
            for subtree in tree.get_subtrees():
                q.put(subtree)
        return None

    def save(self, filepath: Path) -> None:
        """Save the state of this MonteCarloTreeSearcher to a file."""
        with open(filepath, 'wb+') as fp:
            pickle.dump(self, fp)

    @staticmethod
    def load(filepath: Path) -> MonteCarloTreeSearcher:
        """Load a MonteCarloTreeSearcher from a file."""
        with open(filepath, 'rb') as fp:
            return pickle.load(fp)


class MCTSPlayer(Player):
    """A Hearthstone Battlegrounds AI that uses a Monte Carlo tree searcher to pick moves."""
    # Private Instance Attributes
    #   - _mcts: The Montre Carlo tree searcher.
    #   - _iterations: The number of rollouts to perform before making a move.
    #   - _player_index: The index of this player.
    #   - _previous_move_same_count: The number of times the same move has been made.
    #   - _previous_move_same_count: The previous move made.
    _mcts: MonteCarloTreeSearcher
    _iterations: int
    _warmup_iterations: int
    _player_index: int
    _previous_move_same_count: int
    _previous_move: Move
    _cutoff_factor: int
    _cutoff: bool

    def __init__(self, index: int, exploration_weight: float = 2**0.5, iterations: int = 5,
                 mcts: Optional[MonteCarloTreeSearcher] = None, cutoff_factor: int = 10,
                 seed: int = None) -> None:
        """Initialise this MCTSPlayer.

        Preconditions:
            - iterations >= 0
            - warmup_iterations >= 0

        Args:
            index: The index of this player.
            exploration_weight: Exploration weight in the UCT bound.
            iterations: The number of rollouts to perform before making a move.
            mcts: The MonteCarloTreeSearcher instance to use. If None, initialises one instead.
        """
        if seed is None:
            seed = get_seed()

        if mcts is None:
            self._mcts = MonteCarloTreeSearcher(index, exploration_weight=exploration_weight,
                                                seed=seed)
        else:
            self._mcts = mcts

        self._iterations = iterations
        self._player_index = index
        self._previous_move_same_count = 0
        self._previous_move = None
        self._cutoff_factor = cutoff_factor
        self._cutoff = False

    def make_move(self, game: BattlegroundsGame) -> Move:
        """Make a move given the current game.

        Preconditions:
            - There is at least one valid move for the given game
        """
        if not self._cutoff:
            self._train(game, self._iterations)
            tree = self._mcts.choose(game)

            # Update previous move
            if tree.move == self._previous_move:
                self._previous_move_same_count += 1
            else:
                self._previous_move_same_count = 0
            self._previous_move = tree.move

            # Update cutoff
            if self._previous_move_same_count >= self._cutoff_factor:
                self._cutoff = True

            # Make move in a copy
            random.seed(tree.seed)
            game_copy = game.copy_and_make_move(tree.move)

            # Update the tree with the latest game nodes
            state = _DeterministicTavernGameBoard.from_board(game.boards[self._player_index])
            if tree._deterministic_state != state:
                tree.add_subtree(_GameTree(game_copy.boards[self._player_index], tree.move, seed=tree.seed))

            random.seed(tree.seed)
            return tree.move
        else:
            # Act like a random player if we have reached the cutoff`
            return random.choice(game.get_valid_moves())

    def _train(self, game: BattlegroundsGame, n_iterations: int) -> None:
        """Train the Monte Carlo tree searcher by performing the given amount of rollouts
        from the given game state.
        """
        for _ in range(n_iterations):
            self._mcts.rollout(game)


class GreedyPlayer(Player):
    """A Hearthstone Battlegrounds AI that greedily chooses
    the move that maximizes average reward."""
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
        Every player moves randomly."""
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


def run_games(n: int, players: List[Player], show_stats: bool = True, friendly_player: int = 0) \
        -> List[int]:
    """Run n games using the given Players in parallel.
    Return a list of the winners.

    Args:
        n: The number of games to run.
        players: A list of players to run the games with.
        show_stats: Whether to display summary statistics about the games.
        friendly_player: The index of the friendly player.
        seed: THE seed.

    Preconditions:
        - n >= 1
        - len(players) > 0 and len(players) % 2 == 0
    """
    stats = {i: 0 for i in range(len(players))}
    results = [None] * n

    for game_index in range(n):
        winner, _ = run_game(players)
        stats[winner] += 1
        results[game_index] = winner
        print(f'Game {game_index + 1} winner: Player {winner + 1}')

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')

    if show_stats:
        plot_game_statistics(results, friendly_player)

    return results


def run_games_parallel(n: int, players: List[Player], n_jobs: int = 9, use_thread_pool: bool = False,
                      show_stats: bool = True, friendly_player: int = 0, seed: int = None) -> None:
    """Run n games using the given Players in parallel.

    Args:
        n: The number of games to run.
        players: A list of players to run the games with.
        n_jobs: The number of games to run in parallel.
        show_stats: Whether to display summary statistics about the games.
        friendly_player: The index of the friendly player.
        seed: THE seed.

    Preconditions:
        - n >= 1
        - len(players) > 0 and len(players) % 2 == 0
        - n_jobs >= 1
    """
    stats = {i: 0 for i in range(len(players))}
    results = [None] * n

    Executor = ThreadPoolExecutor if use_thread_pool else ProcessPoolExecutor
    with Executor(max_workers=n_jobs) as pool:
        if seed is not None:
            # Initialise this seed
            random.seed(seed)
        futures = [pool.submit(run_game, copy.deepcopy(players)) for _ in range(n)]
        for game_index, future in enumerate(as_completed(futures)):
            winner, _ = future.result()
            stats[winner] += 1
            results[game_index] = winner
            print(f'Game {game_index + 1} winner: Player {winner + 1}')

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')

    if show_stats:
        plot_game_statistics(results, friendly_player)


def run_game(players: List[Player], visualise: bool = False, fps: int = 5) \
        -> Tuple[int, List[Tuple[int, Move]]]:
    """Run a Battlegrounds game between the given players.

    Return the index of the winning player and a list of moves made in the game,
    represented as tuples containing the index of the acting player and the move itself.

    Args:
        players: The agents.
        visualise: Whether to visualise the state of the game.
        fps: The amount of turns to show per second.

    Preconditions:
        - len(players) > 0 and len(players) % 2 == 0

    Implementation notes:
        - We call pygame.time.wait to animate the visualisation (drawing one turn at a time).
          NOTE: You won't be able to close the pygame window while the animation is in
          progress, only after it's done. But you can still stop the Python interpreter
          altogether by clicking the red square button in PyCharm.
    """
    if visualise:
        screen = init_display()
    else:
        screen = None

    game = BattlegroundsGame(num_players=len(players))
    move_sequence = []
    while not game.is_done:
        for index, player in enumerate(players):
            game.start_turn_for_player(index)
            while game.is_turn_in_progress:
                if visualise:
                    draw_game(screen, game, delay=1000 // fps)
                    flip_display()

                move = player.make_move(game)
                game.make_move(move)
                move_sequence.append((index, move))
        game.next_round()

    if visualise:
        close_display()

    return game.winner, move_sequence


def make_game_statistics(results: List[int], friendly_player: int = 0) -> tuple:
    """Return the game statistics."""
    outcomes = [1 if result == friendly_player else 0 for result in results]
    cumulative_win_probability = [sum(outcomes[0:i]) / i for i in range(1, len(outcomes) + 1)]
    rolling_win_probability = \
        [sum(outcomes[max(i - 50, 0):i]) / min(50, i) for i in range(1, len(outcomes) + 1)]
    return outcomes, cumulative_win_probability, rolling_win_probability


def plot_game_statistics(results: List[int], friendly_player: int = 0) -> None:
    """Plot the outcomes and win probabilities for a given list of Battlegrounds game results.

    Preconditions:
        - all(0 <= r < num_players for r in results)
    """
    outcomes, cumulative_win_probability, rolling_win_probability = make_game_statistics(
        results, friendly_player
    )

    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Scatter(y=outcomes, mode='markers',
                             name='Outcome (1 = Friendly player win, 0 = Enemy player win)'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(y=cumulative_win_probability, mode='lines',
                             name='Friendly player win percentage (cumulative)'),
                  row=2, col=1)
    fig.add_trace(go.Scatter(y=rolling_win_probability, mode='lines',
                             name='Friendly player win percentage (most recent 50 games)'),
                  row=2, col=1)
    fig.update_yaxes(range=[0.0, 1.0], row=2, col=1)

    fig.update_layout(title='Battlegrounds Game Results', xaxis_title='Game')
    fig.show()


def save_game_statistics_to_file(filepath: Union[str, Path], results: List[int],
                                 friendly_player: int = 0) -> None:
    """Save the game statistics to the given file."""
    outcomes, cumulative_win_probability, rolling_win_probability = make_game_statistics(
        results, friendly_player
    )
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w+') as fp:
        json.dump({
            'outcomes': outcomes,
            'cum_win_prob': cumulative_win_probability,
            'rolling_win_prob': rolling_win_probability
        }, fp)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['copy', 'random', 'enum', 'contextlib', 'concurrent.futures',
                          'hsbg', 'dill', 'time', 'math', 'pathlib', 'collections', 'queue',
                          'hsbg.visualisation'],
        'allowed-io': ['save', 'load', '_train', 'run_games', 'make_move'],
        'max-line-length': 100,
        'disable': ['E1136', 'E1101', 'R0902', 'R0913', 'W0212', 'E9988', 'R1702']
    })

    # Don't run on this, doesn't like defaultdict
    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()
