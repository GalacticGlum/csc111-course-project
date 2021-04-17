from ai import RandomPlayer, GreedyPlayer, MCTSPlayer, run_game, run_games
from test_ai_framework import test_mcts_player


if __name__ == '__main__':
    """"For a minimal working example, you may simple run one of the experiments."""
    # Simulator Demo
    # ....

    # Test the player implementations against a RandomPlayer via a set of experiments.
    #
    # NOTE: Some of these experiments can take a very long time---patience is key!
    # We recommend keeping n_games as a small value. You should notice that the RandomPlayer
    # VS itself experiment runs the fastest, the MCTS experiment is the second fastest,
    # and the GreedyPlayer is the slowest (by a sizable amount too!), which is in line with
    # the result in our paper.
    #
    # After the set number of moves are complete, this will open a plotly window and display
    # statistics about the game. If you prefer not to, simply set show_stats to False.
    #
    # n_games = 10  # The number of games to run!
    # Experiment 1. Run n games of the RandomPlayer against itself and save the results
    # results = run_games(n_games, [RandomPlayer(), RandomPlayer()], show_stats=True)
    #
    # Experiment 2. Run n games of the MCTSPlayer vs the RandomPlayer and save the results
    # results = test_mcts_player(n_games)
    #
    # Experiment 3. Run n games of the GreedyPlayer vs the RandomPlayer and save the results
    # results = run_games(n_games, [GreedyPlayer(0), RandomPlayer()], show_stats=True)

    # We can also visualise the game as it is played by the agents! To do so, we run a single game
    # with some players, and set visualise to true.
    #
    # For simplicitly, we visualise a game between two RandomPlayers, but feel free to change this.
    # winner, _ = run_game([RandomPlayer(), RandomPlayer()], visualise=True)
    # print(f'Player {winner + 1} won the game!')