import time
import pprint
from hsbg.ai import RandomPlayer, run_game, run_games

# start_time=time.time()
# winner, move_sequence = run_game([RandomPlayer(), RandomPlayer()])
# print(f'Player {winner + 1} won the game!')
# # pprint.pprint(move_sequence)
# print('Took {:.2f} seconds to run a game'.format(time.time() - start_time))

start_time=time.time()
n = 64
run_games(n, [RandomPlayer(), RandomPlayer()], n_jobs=8)
elapsed = time.time() - start_time
print('Took {:.3f} seconds to run {} games ({:.3f} seconds per game)'.format(elapsed, n, elapsed / n))