"""Tests for the AI framework.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import time
import pprint
from hsbg.ai import RandomPlayer, MCTSPlayer, run_game, run_games

if __name__ == '__main__':
    wins = 0
    player = MCTSPlayer(0)
    N_GAMES = 100
    for game_index in range(N_GAMES):
        start_time = time.time()
        winner, move_sequence = run_game([player, RandomPlayer()])
        print(f'Player {winner + 1} won the game!')
        print('Took {:.2f} seconds to run a game'.format(time.time() - start_time))
        if winner == 0:
            wins += 1
        # if game_index > 0 and game_index % 10 == 0:
        #     # Save every 10-th game
        #     save_filepath = f'output/tree_checkpoint_{game_index + 1}'
        #     print(f'Saving current tree state to {save_filepath}')
        #     player._mcts.save(save_filepath)
    print('Player 1 won {:.2f}%% of games'.format(100 * wins / N_GAMES))
    # pprint.pprint(move_sequence)
    player._mcts.save(f'output/tree_final_{N_GAMES}')

    # start_time=time.time()
    # n = 1000
    # run_games(n, [RandomPlayer(), RandomPlayer()], n_jobs=1)
    # elapsed = time.time() - start_time
    # print('Took {:.3f} seconds to run {} games ({:.3f} seconds per game)'.format(elapsed, n, elapsed / n))
