"""A Monte Carlo tree search (MCTS) implementation."""
from __future__ import annotations
import math
import random
from collections import defaultdict
from abc import ABC, abstractmethod, abstractproperty
from typing import List, Set, Dict, Callable, Optional

from hsbg import BattlegroundsGame, Move


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
    _total_rewards: Dict[BattlegroundsGame, int]
    _visit_counts: Dict[BattlegroundsGame, int]
    _children: Dict[BattlegroundsGame, Set[BattlegroundsGame]]

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
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

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

    def _simulate(self, game: BattlegroundsGame) -> float:
        """Return the reward for a random simulation from the given game state."""
        while True:
            if game.is_done:
                winning_player = game.winner
                assert winning_player is not None
                # The friendly player is denoted with index 0!
                # Reward of 1 if the friendly player won, and 0 if they lost.
                reward = 1 if winning_player == 0 else 0
                return 1 - reward if game.active_player == 0 else reward
            game = MonteCarloTreeSearcher._get_random_successor(game)

    def _backpropagate(self, path: List[BattlegroundsGame], reward: float) -> None:
        """Propogate the reward up the given path. This is a classical monte carlo update."""
        for game in reversed(path):
            self._visit_counts[game] += 1
            # Add reward, making sure to invert if this game represents the enemy player
            r = (reward if game.active_player == 0 else 1 - reward)
            self._total_rewards[game] += r

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
    def _get_successor(game: BattlegroundsGame, move: Move) -> BattlegroundsGame:
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
