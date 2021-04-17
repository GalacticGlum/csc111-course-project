import time
import copy
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
for _ in range(50):
    game = BattlegroundsGame(num_players=2)
    random.seed(seed)

    previous_move = None
    previous_move_same_count = 0
    use_tree = True

    while not game.is_done:
        game.start_turn_for_player(0)
        while game.is_turn_in_progress:
            # a = game.boards[0].as_format_str()
            # print(a)
            # print(mcts._game_tree)
            try:
                if use_tree:
                    for _ in range(1):
                        mcts.rollout(game)
                    # print(mcts._game_tree)

                    tree = mcts.choose(game)

                    random.seed(tree._seed)
                    # print(f'Move {tree.move}')
                    game.make_move(tree.move)

                    if tree.move == previous_move:
                        previous_move_same_count += 1
                    else:
                        previous_move_same_count = 0
                    previous_move = tree.move

                    if previous_move_same_count >= 10:
                        use_tree = False
                        # print(mcts._game_tree)

                    # print(tree)
                    # print(mcts._game_tree)

                    # state = _DeterministicTavernGameBoard.from_board(game.boards[0])
                    state = _DeterministicTavernGameBoard.from_board(game.boards[0])
                    # should_add = all(state != subtree._deterministic_state for subtree in tree.get_subtrees())
                    if tree._deterministic_state != state:
                        new_tree = _GameTree(copy.deepcopy(game.boards[0]), tree.move, seed=tree._seed)
                        tree.add_subtree(new_tree)
                else:
                    move = random.choice(game.get_valid_moves())
                    game.make_move(move)

                # Loop Invariant: The game state after making the move represented by tree should be a subtree of tree.
                # assert any(state == subtree._deterministic_state for subtree in tree.get_subtrees())

            except Exception as e:
                with open('mcts_error.txt', 'w+') as fp:
                    fp.write(str(tree))
                    fp.write(game.boards[0].as_format_str())
                raise e

        game.start_turn_for_player(1)
        while game.is_turn_in_progress:
            game.make_move(random.choice(game.get_valid_moves()))
        game.next_round()
    print(f'Player {game.winner + 1} won')