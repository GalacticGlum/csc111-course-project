"""Tests for the combat phase.
These are just a collection of different battles that always have the same result
(no matter the random move taken).
"""
from hsbg import TavernGameBoard, minions


def test_battle_1() -> None:
    """
    Test a battle with the following configuration:
        board
        * Tabbycat
        * Scavenging Hyena
        vs
        * Tabbycat
        * Tabbycat
        * Tabbycat
    The friendly player should win.
    """
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.TABBYCAT)
    friendly_board.add_minion_to_hand(minions.SCAVENGING_HYENA)
    friendly_board.play_minion(0)
    friendly_board.play_minion(1)

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.play_minion(0)
    enemy_board.play_minion(1)
    enemy_board.play_minion(2)

    battle = friendly_board.battle(enemy_board)
    assert battle.win_probability == 1