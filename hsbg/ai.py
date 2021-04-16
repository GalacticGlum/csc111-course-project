"""Framework for making Hearthstone Battlegrounds AI."""
from __future__ import annotations
import copy
import time
import math
import random
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Tuple, List, FrozenSet, Set, Dict, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import colorama
import dill as pickle

from hsbg.utils import colourise_string
from hsbg import BattlegroundsGame, TavernGameBoard, Move


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
    """This is a simplified representation of the TavernGameBoard.
    Note that minions are stored as a string representation.

    Instance Attributes:
        - tavern_tier: The tier of the tavern.
        - hero_health: The health of the hero.
        - gold: The amount of gold available.
        - is_frozen: Whether the recruits are frozen.
        - hand: The minions in the hand.
        - board: The minions on the board.
        - recruits: The minions available for purchase.
        - valid_moves: A list of valid moves from this board state.
    """
    tavern_tier: int
    hero_health: int
    gold: int
    is_frozen: bool
    hand: FrozenSet[str]
    board: FrozenSet[str]
    recruits: FrozenSet[str]
    valid_moves: List[Move]

    @staticmethod
    def from_game(board: TavernGameBoard) -> _CompactGameState:
        """Return a game tree node for the given TavernGameBoard."""
        return _CompactGameState(
            board.tavern_tier,
            board.hero_health,
            board.gold,
            board.is_frozen,
            frozenset({str(x) for x in board.get_minions_in_hand()}),
            frozenset({str(x) for x in board.get_minions_on_board()}),
            frozenset({str(x) for x in board.recuits if x is not None}),
            board.get_valid_moves()
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
    _subtrees: List[_GameTree]

    def __init__(self, board: Optional[TavernGameBoard] = None, move: Optional[Move] = None) \
            -> None:
        """Initialize a new game tree."""
        self.board = board or TavernGameBoard()
        if board is None:
            self.board.next_turn()

        self.move = move
        self.visit_count = 0
        self.total_reward = 0
        self._subtrees = []

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

    def _get_uct(self, exploration_weight: float = 2**0.5) -> float:
        """Return the upper confidence bound for this tree."""
        exploration_coefficient = math.sqrt(math.log(self.visit_count) / self.visit_count)
        return self.average_reward + exploration_weight * exploration_coefficient

    def uct_select(self) -> _GameTree:
        """Return a subtree of this tree which maximizes the upper confidence bound."""
        # All subtrees should already be expanded
        assert all(x.expanded for x in self._subtrees)
        return max(self._subtrees, key=self._get_uct)

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

    def get_possible_subtrees(self) -> Set[_GameTree]:
        """Return all the possible subtrees from this tree."""
        return {
            self._make_subtree_from_move(move)
            for move in self.board.get_valid_moves()
        }

    def get_random_possible_subtree(self) -> _GameTree:
        """Return a random subtree of this tree."""
        move = random.choice(self.board.get_valid_moves())
        return self._make_subtree_from_move(move)

    def _make_subtree_from_move(self, move: Move) -> _GameTreeNode:
        """Return the subtree representing this tree after making the given move."""
        board_copy = self.board.copy_and_make_move(move)
        board_copy.next_turn()
        return _GameTree(board_copy, move)

    def __str__(self) -> str:
        """Return a string representation of this tree."""
        return self._str_indented(0)

    def _str_indented(self, depth: int) -> str:
        """Return an indented string representation of this tree.

        The indentation level is specified by the <depth> parameter.
        """
        move_desc = f'{self._move_str()} -> '
        s = '    ' * depth + move_desc
        s += self._board_str(len(s)) + '\n'
        if self._subtrees == []:
            return s
        else:
            for subtree in self._subtrees:
                s += subtree._str_indented(depth + 1)
            return s

    def _board_str(self, offset: int = 0) -> str:
        """Return an indented string representation of the board for this tree."""
        board = self.board

        health = colourise_string(f'health {board.hero_health}', colorama.Fore.LIGHTRED_EX)
        turn = colourise_string(f'turn {board.turn_number}', colorama.Fore.LIGHTBLUE_EX)
        tier = colourise_string(f'tier {board.tavern_tier}', colorama.Fore.LIGHTCYAN_EX)
        gold = colourise_string(f'{board.gold} gold', colorama.Fore.YELLOW)

        recruit_label = colourise_string('recruits: ', colorama.Fore.LIGHTBLACK_EX)
        board_label = colourise_string('board: ', colorama.Fore.LIGHTBLACK_EX)
        hand_label = colourise_string('hand: ', colorama.Fore.LIGHTBLACK_EX)

        def _colourise_minion(minion: Optional[Minion]) -> str:
            """Return a colourised string representation of the given minion."""
            if minion is None:
                return colourise_string('(empty)', colorama.Fore.LIGHTBLACK_EX)
            else:
                return colourise_string(f'({str(minion)})', colorama.Fore.LIGHTWHITE_EX)

        lines = [
            f'{turn}, {health}, {tier}, {gold}',
            recruit_label + ', '.join(_colourise_minion(x) for x in board.recruits),
            board_label + ', '.join(_colourise_minion(x) for x in board.board),
            hand_label + ', '.join(_colourise_minion(x) for x in board.hand)
        ]
        return '\n'.join(
            (offset if index > 0 else 0) * ' ' + line
            for index, line in enumerate(lines)
        )

    def _move_str(self) -> str:
        """Return a string representation of the move for this tree."""
        if self.move is None:
            return str(None)
        else:
            return f'({self.move.action.name}, index={self.move.index})'


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

    def __init__(self, friendly_player: int, exploration_weight: float = 2**0.5) -> None:
        """Initialise a new MonteCarloTreeSearcher."""
        self.exploration_weight = exploration_weight
        self._game_tree = _GameTree()
        self._friendly_player = friendly_player

    def choose(self, game: BattlegroundsGame,
               metric: Optional[Callable[[_GameTreeNode], float]] = None) -> _GameTreeNode:
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

        node = self._make_node_from_game(game)
        if node not in self._children:
            return self._get_random_successor(node)

        metric = metric or self._average_reward
        return max(self._children[node], key=metric)

    def rollout(self, game: BattlegroundsGame) -> None:
        """Rollout the tree from the given game state."""
        node = self._make_node_from_game(game)
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)

        for p in path:
            print(game.active_player, p.board==game.boards[self._friendly_player])
            if p.move is None:
                print(p)
                continue
            print(p.move)
            game = game.copy_and_make_move(p.move)

        reward = self._simulate(game)
        self._backpropagate(path, reward)

    def _select(self, tree: _GameTree) -> List[_GameTree]:
        """Return a path to an unexplored descendent of the given node."""
        path = []
        while True:
            path.append(tree)
            if tree.get_subtrees() == []:
                # We've reached a leaf node, so we are done.
                return path
            unexplored = [subtreee for subtree in tree.get_subtrees() if not subtree.expanded]
            if unexplored:
                # Select any uunexplored child, and we are done!
                path.append(unexplored.pop())
                return path
            else:
                # Select a node according to the upper confidence bound.
                tree = tree.uct_select()

    def _simulate(self, game: BattlegroundsGame) -> int:
        """Return the reward for a random simulation of the given game until completion."""
        game.clear_turn_completion()
        while game.winner is None:
            for index in game.alive_players:
                game.start_turn_for_player(index)
                while game.is_turn_in_progress:
                    move = random.choice(game.get_valid_moves())
                    game.make_move(move)
            game.next_round()

        # A reward of 1 if we win, and 0 if we lose.
        reward = int(game.winner == self._friendly_player)
        return reward

    def _backpropagate(self, path: List[_GameTree], reward: int) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for tree in reversed(path):
            tree.total_reward += reward
            tree.visit_count += 1

    def _make_node_from_game(self, game: BattlegroundsGame) -> _GameTreeNode:
        """Return the _GameTreeNode corresponding to the given game."""
        # Get the move that led to this state
        move_history = game._move_history[self._friendly_player]
        if move_history:
            move = move_history[-1]
        else:
            move = None
        return _GameTreeNode(game.boards[self._friendly_player], move)

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
    #   - _warmup_iterations: The number of rollouts to perform before making a move.
    _mcts: MonteCarloTreeSearcher
    _iterations: int
    _warmup_iterations: int

    def __init__(self, index: int, exploration_weight: float = 2**0.5, iterations: int = 2,
                 warmup_iterations: int = 0, mcts: Optional[MonteCarloTreeSearcher] = None) -> None:
        """Initialise this MCTSPlayer.

        Preconditions:
            - iterations >= 0
            - warmup_iterations >= 0

        Args:
            index: The index of this player.
            exploration_weight: Exploration weight in the UCT bound.
            iterations: The number of rollouts to perform before making a move.
            warmup_iterations: The number of rollouts to perform when initialising the tree.
            mcts: The MonteCarloTreeSearcher instance to use. If None, initialises one instead.
        """
        if mcts is None:
            self._mcts = MonteCarloTreeSearcher(index, exploration_weight=exploration_weight)
        else:
            self._mcts = mcts
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
        print('chose: ', node.move)
        return node.move

    def _train(self, game: BattlegroundsGame, n_iterations: int) -> None:
        """Train the Monte Carlo tree searcher by performing the given amount of rollouts
        from the given game state.
        """
        if n_iterations == 0:
            return

        start_time = time.time()
        for _ in range(n_iterations):
            print(f'rolling out on {game.active_player}')
            self._mcts.rollout(game)
        elapsed_time = time.time() - start_time
        print('Finished rollout in {:.2f} seconds ({:.2f} seconds per rollout)'.format(
            elapsed_time, elapsed_time / n_iterations
        ))


class GreedyPlayer(Player):
    """A Hearthstone Battlegrounds AI that greedily chooses the move that maximizes average reward."""
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
            for game_index in range(self._games_per_move):
                game_copy = game.copy_and_make_move(move)
                total_reward += self._simulate(game_copy)

            average_reward = total_reward / self._games_per_move
            if average_reward > best_reward:
                best_reward = average_reward
                best_move_yet = move

        return best_move_yet

    def _simulate(self, game: BattlegroundsGame) -> int:
        """Return the reward for a random simulation from the given game. Every player moves randomly."""
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
        futures = [pool.submit(run_game, copy.deepcopy(players)) for b in range(n)]
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['copy', 'random', 'enum', 'contextlib', 'concurrent.futures',
    #                       'hsbg', 'dill', 'time', 'math', 'pathlib', 'collections'],
    #     'allowed-io': ['save', 'load', '_train', 'run_games'],
    #     'max-line-length': 100,
    #     'disable': ['E1136', 'E1101', 'R0902', 'R0913', 'W0212']
    # })

    # Don't run on this, doesn't like defaultdict
    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()
