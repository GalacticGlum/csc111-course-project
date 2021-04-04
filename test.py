import time
import pprint
from hsbg.ai import RandomPlayer, run_game, run_games

winner, move_sequence = run_game([RandomPlayer(), RandomPlayer()])
print(f'Player {winner + 1} won the game!')
# pprint.pprint(move_sequence)

# start_time=time.time()
# n = 100
# run_games(n, [RandomPlayer(), RandomPlayer()], n_jobs=100)
# print('Took {:.2f} seconds to run {} games'.format(time.time() - start_time, n))