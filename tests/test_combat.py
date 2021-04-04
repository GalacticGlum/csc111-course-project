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
    assert battle.win_probability == 1 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 0
    # Test that the battle for the enemy board has the opposite stats
    battle = enemy_board._battle_history[-1]
    assert battle.win_probability == 0 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 1
    assert friendly_board.won_previous and not enemy_board.won_previous


def test_battle_2() -> None:
    """
    Test a battle with the following configuration:
        board
        * Pack Leader
        * Alleycat
        * Tabbycat
        * Kindly Grandmother
        * Scavenging Hyena
        vs
        * Murloc Tidecaller
        * Murloc Tidehunter
        * Murloc Scout
        * Rockpool Hunter
    The friendly player should win.
    """
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.PACK_LEADER)
    friendly_board.add_minion_to_hand(minions.ALLEYCAT)
    friendly_board.add_minion_to_hand(minions.KINDLY_GRANDMOTHER)
    friendly_board.add_minion_to_hand(minions.SCAVENGING_HYENA)
    friendly_board.play_minion(0)
    friendly_board.play_minion(1)
    friendly_board.play_minion(2)
    friendly_board.play_minion(3)

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    enemy_board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER)
    enemy_board.add_minion_to_hand(minions.MURLOC_SCOUT)
    enemy_board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    friendly_board.play_minion(0)
    friendly_board.play_minion(1)
    friendly_board.play_minion(2)
    friendly_board.play_minion(3)

    battle = friendly_board.battle(enemy_board)
    assert battle.win_probability == 1 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 0
    # Test that the battle for the enemy board has the opposite stats
    battle = enemy_board._battle_history[-1]
    assert battle.win_probability == 0 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 1
    assert friendly_board.won_previous and not enemy_board.won_previous


def test_battle_3() -> None:
    """
    Test a battle with the following configuration:
        board
        * Imp Gang Boss
        * Nathrezim Overseer
        * Infested Wolf
        * Houndmaster
        vs
        * Harvest Golem
        * Kaboom Bot
        * Metaltooth Leaper
        * Screwjank Clunker
        * Khadgar
        * Savannah Highmane
    The friendly player should lose.
    """
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    friendly_board.add_minion_to_hand(minions.NATHREZIM_OVERSEER)
    friendly_board.add_minion_to_hand(minions.INFESTED_WOLF)
    friendly_board.add_minion_to_hand(minions.HOUNDMASTER)
    friendly_board.play_minion(0)
    friendly_board.play_minion(1)
    friendly_board.play_minion(2)
    friendly_board.play_minion(3)

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.HARVEST_GOLEM)
    enemy_board.add_minion_to_hand(minions.KABOOM_BOT)
    enemy_board.add_minion_to_hand(minions.METALTOOTH_LEAPER)
    enemy_board.add_minion_to_hand(minions.SCREWJANK_CLUNKER)
    enemy_board.add_minion_to_hand(minions.KHADGAR)
    enemy_board.add_minion_to_hand(minions.SAVANNAH_HIGHMANE)
    enemy_board.play_minion(0)
    enemy_board.play_minion(1)
    enemy_board.play_minion(2)
    enemy_board.play_minion(3)
    enemy_board.play_minion(4)
    enemy_board.play_minion(5)

    battle = friendly_board.battle(enemy_board)
    assert battle.win_probability == 0 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 1
    # Test that the battle for the enemy board has the opposite stats
    battle = enemy_board._battle_history[-1]
    assert battle.win_probability == 1 and battle.tie_probability == 0 \
                                       and battle.lose_probability == 0
    assert not friendly_board.won_previous and enemy_board.won_previous
