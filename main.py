"""Main file for running the program.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""

from ai import (
    RandomPlayer, GreedyPlayer, MCTSPlayer,
    run_game, run_games,
    _GameTree
)
from test_ai_framework import test_mcts_player
from visualisation import visualise_game_board

if __name__ == '__main__':
    """"For a minimal working example, you may simple run one of the experiments."""
    # We can manipulate a Hearthstone Battlegrounds game using the simulator API.
    # Here is a short example highlighting how we can mutate the board state, and
    # perform actions on the board.
    #
    # from hsbg import TavernGameBoard
    # board = TavernGameBoard()  # This is an empty board!
    # board.next_turn()  # Start the first turn
    # board.buy_minion(0)  # Buy the minion at index 0, and insert it to the hand.
    # board.play_minion(0)  # Play a minion from the hand at index 0.
    # from minions import MURLOC_SCOUT
    # board.summon_minion(MURLOC_SCOUT.clone())
    # board.next_turn()  # End the turn
    # # ...
    # # Show the game board state.
    # visualise_game_board(board)

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
    n_games = 10  # The number of games to run!
    # Experiment 1. Run n games of the RandomPlayer against itself and save the results
    # results = run_games(n_games, [RandomPlayer(), RandomPlayer()], show_stats=False)
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
    # Please refrain from clicking while the visualization is running!
    # winner, _ = run_game([RandomPlayer(), RandomPlayer()], visualise=True)
    # print(f'Player {winner + 1} won the game!')

    # Finally, we can also visualise the _GameTree class! In this example, we create an
    # _GameTree and then expand it a few times.
    #
    # Sit back and enjoy the pretty colours!
    # tree = _GameTree()
    # for _ in range(5):
    #     # Get a leaf
    #     leaf = tree.select()[-1]
    #     # Expand the leaf
    #     leaf.expand()
    # # Print the whole tree after expanding!
    # print(tree)
