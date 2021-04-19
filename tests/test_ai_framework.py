"""Tests for the AI framework.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import random
from hsbg.ai import (
    RandomPlayer, GreedyPlayer,
    run_game, run_games,
    plot_game_statistics,
)


if __name__ == '__main__':
    # Benchmark the simulator with multithreadaing.
    import time
    start_time = time.time()

    N_GAMES = 10000
    run_games(N_GAMES, [RandomPlayer(), RandomPlayer()], show_stats=False, n_jobs=8)
    elapsed = time.time() - start_time
    print('Took {} seconds ({} seconds/game, {} games/seconds).'.format(
        elapsed, elapsed / N_GAMES, N_GAMES / elapsed
    ))
