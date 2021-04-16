import time
import pprint
from hsbg.ai import RandomPlayer, GreedyPlayer, MCTSPlayer, run_game, run_games

if __name__ == '__main__':
    player = MCTSPlayer(0)
    wins = 0
    N_GAMES = 20
    for game_index in range(N_GAMES):
        start_time=time.time()
        winner, move_sequence = run_game([player, RandomPlayer()])
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
