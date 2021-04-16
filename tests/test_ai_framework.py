import time
import pprint
from hsbg.ai import RandomPlayer, MCTSPlayer, run_game, run_games

if __name__ == '__main__':
    wins = 0
    N_GAMES = 100
    for _ in range(N_GAMES):
        start_time=time.time()
        player = MCTSPlayer(0)
        winner, move_sequence = run_game([player, RandomPlayer()])
        print(f'Player {winner + 1} won the game!')
        print('Took {:.2f} seconds to run a game'.format(time.time() - start_time))
        if winner == 0:
            wins+=1
    print('Player 1 won {:.2f}%% of games'.format(wins / N_GAMES))
        # pprint.pprint(move_sequence)


    # start_time=time.time()
    # n = 1000
    # run_games(n, [RandomPlayer(), RandomPlayer()], n_jobs=1)
    # elapsed = time.time() - start_time
    # print('Took {:.3f} seconds to run {} games ({:.3f} seconds per game)'.format(elapsed, n, elapsed / n))