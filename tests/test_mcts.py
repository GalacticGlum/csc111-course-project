import time
import random
from hsbg import BattlegroundsGame
from hsbg.ai import MonteCarloTreeSearcher, _GameTree, _DeterministicTavernGameBoard

# We use the current time as the seed rather than letting numpy seed
# since we want to achieve consistent results across sessions.
# Source: https://stackoverflow.com/a/45573061/7614083
t = int(time.time() * 1000.0)
seed = ((t & 0xff000000) >> 24) + ((t & 0x00ff0000) >> 8) + ((t & 0x0000ff00) <<  8) + ((t & 0x000000ff) << 24)

# random.seed(seed)
mcts = MonteCarloTreeSearcher(0, seed=seed)
for _ in range(10):
    game = BattlegroundsGame(num_players=2)
    previous_moves = []

    random.seed(seed)

    while not game.is_done:
        game.start_turn_for_player(0)
        while game.is_turn_in_progress:
            # a = game.boards[0].as_format_str()
            # print(a)
            # print(mcts._game_tree)

            try:
                for _ in range(1):
                    mcts.rollout(game)
                # print(mcts._game_tree)
                tree = mcts.choose(game)
                random.seed(tree._seed)
                # print(f'Move {tree.move}')
                game.make_move(tree.move)
                previous_moves.append(tree.move)
                if previous_moves[:10].count(tree.move) == 10:
                    print(tree)
                    exit(1)

                # state = _DeterministicTavernGameBoard.from_board(game.boards[0])
                if mcts.get_tree_from_board(game.boards[0]) is None:
                    tree.add_subtree(_GameTree(game.boards[0], tree.move, seed=tree._seed))
            except Exception as e:
                print(tree)
                print(game.boards[0].as_format_str())
                raise e

        game.start_turn_for_player(1)
        while game.is_turn_in_progress:
            game.make_move(random.choice(game.get_valid_moves()))
        game.next_round()
    print(f'Player {game.winner + 1} won')