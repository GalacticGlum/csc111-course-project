import time
import random
from hsbg import BattlegroundsGame
from hsbg.ai import MonteCarloTreeSearcher

# We use the current time as the seed rather than letting numpy seed
# since we want to achieve consistent results across sessions.
# Source: https://stackoverflow.com/a/45573061/7614083
t = int(time.time() * 1000.0)
seed = ((t & 0xff000000) >> 24) + ((t & 0x00ff0000) >> 8) + ((t & 0x0000ff00) <<  8) + ((t & 0x000000ff) << 24)

mcts = MonteCarloTreeSearcher(0, seed=seed)
game = BattlegroundsGame(num_players=2)

random.seed(seed)
game.start_turn_for_player(0)
a = game.boards[0].as_format_str()
b = mcts._game_tree.board.as_format_str()

# print(a)
# print(b)

# game.boards[0].refresh_recruits()
# mcts._game_tree.board.refresh_recruits()

tree = mcts.choose(game)
for _ in range(50):
    mcts.rollout(game)
# print(mcts._game_tree)

random.seed(tree._seed)
game.make_move(tree.move)
print(f'Move {tree.move}')
print(game.boards[0].as_format_str())