import time
import pprint
from hsbg.ai import RandomPlayer, MCTSPlayer, run_game, run_games

if __name__ == '__main__':
    start_time=time.time()
    winner, move_sequence = run_game([MCTSPlayer(0), RandomPlayer()])
    print(f'Player {winner + 1} won the game!')
    print('Took {:.2f} seconds to run a game'.format(time.time() - start_time))
    pprint.pprint(move_sequence)

    # start_time=time.time()
    # n = 1000
    # run_games(n, [RandomPlayer(), MCTSPlayer()], n_jobs=1)
    # elapsed = time.time() - start_time
    # print('Took {:.3f} seconds to run {} games ({:.3f} seconds per game)'.format(elapsed, n, elapsed / n))