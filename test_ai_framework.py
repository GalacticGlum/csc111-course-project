"""Tests for the AI framework.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import random
from utils import get_seed
from ai import (
    RandomPlayer, GreedyPlayer, MCTSPlayer,
    run_game, run_games,
    plot_game_statistics,
    save_game_statistics_to_file
)


def test_mcts_player(n: int, show_stats: bool = True) -> list:
    """Run n games of the MCTSPlayer against the RandomPlayer.

    Args:
        n: The number of games to run.
        show_stats: Whether to display summary statistics about the games.

    Preconditions:
        - n >= 1
    """
    stats = {i: 0 for i in range(2)}
    results = [None] * n

    for game_index in range(n):
        seed = get_seed()
        player = MCTSPlayer(0, seed=seed)

        random.seed(seed)
        winner, _ = run_game([player, RandomPlayer()])

        stats[winner] += 1
        results[game_index] = winner
        print(f'Game {game_index + 1} winner: Player {winner + 1}')

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')

    if show_stats:
        plot_game_statistics(results, 0)

    return results
