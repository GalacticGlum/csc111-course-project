"""Tests for the AI framework.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import time
import pprint
from hsbg.ai import RandomPlayer, GreedyPlayer, MCTSPlayer, MonteCarloTreeSearcher, run_game, run_games

# We use the current time as the seed rather than letting numpy seed
# since we want to achieve consistent results across sessions.
# Source: https://stackoverflow.com/a/45573061/7614083
t = int(time.time() * 1000.0)
seed = ((t & 0xff000000) >> 24) + ((t & 0x00ff0000) >> 8) + ((t & 0x0000ff00) <<  8) + ((t & 0x000000ff) << 24)

if __name__ == '__main__':
    mcts = MonteCarloTreeSearcher(0, seed=seed)
    player = MCTSPlayer(0, mcts=mcts)
    wins = 0
    N_GAMES = 20
    for game_index in range(N_GAMES):
        start_time=time.time()
        winner, move_sequence = run_game([player, RandomPlayer()], seed=seed)
        print(f'Player {winner + 1} won the game!')
        print('Took {:.2f} seconds to run a game'.format(time.time() - start_time))
        if winner == 0:
            wins+=1
    print('Player 1 won {:.2f}%% of games'.format(100 * wins / N_GAMES))
    # pprint.pprint(move_sequence)
    # player._mcts.save(f'output/tree_final_{N_GAMES}')

    # start_time=time.time()
    # n = 100
    # run_games(n, [GreedyPlayer(0), RandomPlayer()], n_jobs=8)
    # elapsed = time.time() - start_time
    # print('Took {:.3f} seconds to run {} games ({:.3f} seconds per game)'.format(elapsed, n, elapsed / n))
