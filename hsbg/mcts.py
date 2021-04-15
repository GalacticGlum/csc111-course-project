"""A Monte Carlo tree search (MCTS) implementation."""
from __future__ import annotations
import math
from collections import defaultdict
from abc import ABC, abstractmethod, abstractproperty
from typing import List, Set, Dict, Callable, Optional


class GameState(ABC):
    """A representation of the state of a two-player game."""
    @abstractmethod
    def get_successors(self) -> Set[GameState]:
        """Return a set of all possible successors from this game state."""
        return set()

    @abstractmethod
    def get_random_successor(self) -> Optional[GameState]:
        """Return a random successor of this game state."""
        return None

    def reward(self) -> float:
        """Return the reward of this game state in a [0, 1] interval.
        Raise a ValueError if this game state is not done."""
        return 0

    @abstractproperty
    def is_done(self) -> bool:
        """Return whether the game is done (has no successors)."""
        return True

    @abstractproperty
    def is_friendly_player(self) -> bool:
        """Return whether it is currently the friendly players' turn."""
        return True

    @abstractmethod
    def __hash__(self):
        """Return the hash of this game state."""
        return 123456789

    @abstractmethod
    def __eq__(a: GameState, b: GameState) -> bool:
        """Return whether the two game states are equal."""
        return True


class MCTS:
    """A Monte Carlo tree searcher for a two-player turn-based game.

    Instance Attributes:
        - exploration_weight: The exploration parameter (c) in the upper confidence bound.
    """
    # Private Instance Attributes:
    #   - _total_rewards: A dict mapping the total reward of each node.
    #   - _visit_counts: A dict mapping the total visit count for each node.
    #   - _children: A dict mapping the children of each node.
    exploration_weight: float
    _total_rewards: Dict[GameState, int]
    _visit_counts: Dict[GameState, int]
    _children: Dict[GameState, Set[GameState]]

    def __init__(self, exploration_weight: float = 2**0.5):
        self.exploration_weight = exploration_weight
        self._total_rewards = defaultdict(int)
        self._visit_counts = defaultdict(int)
        self._children = dict()

    def choose(self, node: GameState, metric: Optional[Callable[[GameState], float]] = None) \
            -> GameState:
        """Return the best successor of the given node according to the given metric function
        That is, find a child of the given node which maximizes the given metric.

        Raise a ValueError if the given node is a terminal node.

        Args:
            node: The node whose children to select from.
            metric: A function which takes in a node as input and returns a numerical score
                    measuring the fitness (i.e. the 'goodness') of the node. Defaults to the
                    average reward of the node.
        """
        if node.is_done:
            raise ValueError(f'choose called on terminal node {node}')

        if node not in self._children:
            return node.get_random_successor()

        metric = metric or self._average_reward
        return max(self._children[node], key=metric)

    def _average_reward(self, node: GameState) -> float:
        """Return the average reward of the given node.
        Return ``float(-inf)`` (negative infinity) if the node has not been visited.
        """
        if self._visit_counts[node] == 0:
            return float('-inf')
        else:
            return self._total_rewards[node] / self._visit_counts[node]

    def rollout(self, node: GameState) -> None:
        """Rollout the tree from the given node."""
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node: GameState) -> List[GameState]:
        """Return a path to an unexplored descendent of the given node."""
        path = []
        while True:
            path.append(node)
            if node not in self._children or not self._children[node]:
                # The current node is either unexplored, or a terminal node.
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

    def _expand(self, node: GameState) -> None:
        """Expand the tree at the given node with the possible moves from the game state
        represented by the given node.
        """
        if node in self._children:
            return
        else:
            self._children[node] = node.get_successors()

    def _simulate(self, node: GameState) -> float:
        """Return the reward for a random simulation of the game from the given node."""
        while True:
            if node.is_done:
                reward = node.reward()
                return 1 - reward if node.is_friendly_player else reward
            node = node.get_random_successor()

    def _backpropagate(self, path: List[GameState], reward: float) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for node in reversed(path):
            self._visit_counts[node] += 1
            # Add reward, making sure to invert if this node represents the enemy player
            r = (reward if node.is_friendly_player else 1 - reward)
            self._total_rewards[node] += r

    def _uct_select(self, node: GameState) -> GameState:
        """Return a child of the given node which maximizes the upper confidence bound."""
        # All children of node should already be expanded
        assert all(x in self._children for x in self._children[node])

        log_visit_count = math.log(self._visit_counts[node])
        def _uct(n: GameState) -> float:
            """Return the upper confidence bound for the given node."""
            exploration_coefficient = math.sqrt(log_visit_count / self._visit_counts[n])
            return self._average_reward(n) + self.exploration_weight * exploration_coefficient

        return max(self._children[node], key=_uct)
