import hsbg
import hsbg.combat

game = hsbg.BattlegroundsGame(num_players=2)

while not game.is_done:
    with game.turn_for_player(0) as board:
        if board.turn_number == 1:
            board.add_minion_to_hand(hsbg.minions.MURLOC_SCOUT)
            board.play_minion(0)

    with game.turn_for_player(1) as board:
        if board.turn_number == 1:
            board.add_minion_to_hand(hsbg.minions.ALLEY_CAT)
            board.play_minion(0)

    print(f'Round #{game.round_number}: {game.boards[0].hero_health} hp vs {game.boards[1].hero_health} hp')
    game.next_round()