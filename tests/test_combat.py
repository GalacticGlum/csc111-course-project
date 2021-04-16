"""Tests for the combat phase.
These are just a collection of different battles that always have the same result
(no matter the random move taken).
"""
import pytest
from hsbg.models import Buff, CardAbility
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

    # Test state of the friendly board after playing all minions
    assert friendly_board.get_minions_on_board() == [
        minions.TABBYCAT,
        minions.SCAVENGING_HYENA
    ]

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.add_minion_to_hand(minions.TABBYCAT)
    enemy_board.play_minion(0)
    enemy_board.play_minion(1)
    enemy_board.play_minion(2)

    # Test state of the enemy board after playing all minions
    assert enemy_board.get_minions_on_board() == [minions.TABBYCAT_GOLDEN]

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
        * Kindly Grandmother
        * Scavenging Hyena
        vs
        * Murloc Tidecaller
        * Murloc Tidehunter
        * Murloc Scout
        * Old Murk-Eye
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

    # Test state of the friendly board after playing all minions
    tabbycat = minions.TABBYCAT.clone()
    tabbycat.add_buff(Buff(2, 0, CardAbility.NONE))
    assert friendly_board.get_minions_on_board() == [
        minions.PACK_LEADER,
        minions.ALLEYCAT,
        tabbycat,
        minions.KINDLY_GRANDMOTHER,
        minions.SCAVENGING_HYENA
    ]

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    enemy_board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER)
    enemy_board.add_minion_to_hand(minions.MURLOC_SCOUT)
    enemy_board.add_minion_to_hand(minions.OLD_MURK_EYE)
    enemy_board.play_minion(0)
    enemy_board.play_minion(1)
    enemy_board.play_minion(2)
    enemy_board.play_minion(3)

    # Test state of the enemy board after playing all minions
    murloc_tidecaller = minions.MURLOC_TIDECALLER.clone()
    murloc_tidecaller.add_buff(Buff(1, 0, CardAbility.NONE))
    assert enemy_board.get_minions_on_board() == [
        murloc_tidecaller,
        minions.MURLOC_TIDEHUNTER,
        minions.MURLOC_SCOUT,
        minions.MURLOC_SCOUT,
        minions.OLD_MURK_EYE
    ]

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
