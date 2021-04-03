"""Test the minion implementations."""
import random

from hsbg.models import CardAbility, Buff
from hsbg import TavernGameBoard, minions


def test_alleycat_battlecry() -> None:
    """Test the battlecry for the Alleycat minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.ALLEYCAT)
    board.play_minion(0)
    assert board.get_minions_on_board() == [minions.ALLEYCAT, minions.TABBYCAT]


def test_golden_alleycat_battlecry() -> None:
    """Test the battlecry for the golden Alleycat minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.ALLEYCAT_GOLDEN)
    board.play_minion(0)
    assert board.get_minions_on_board() == [minions.ALLEYCAT_GOLDEN, minions.TABBYCAT_GOLDEN]


def test_vulgar_homunculus_battlecry() -> None:
    """Test the battlecry effect for the Vulgar Homunculus minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.VULGAR_HOMUNCULUS)
    board.play_minion(0)
    # The minion deals 2 damage to the hero when played.
    assert board.hero_health == 38


def test_golden_vulgar_homunculus_battlecry() -> None:
    """Test the battlecry effect for the golden Vulgar Homunculus minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.VULGAR_HOMUNCULUS_GOLDEN)
    board.play_minion(0)
    # The minion deals 2 damage to the hero when played.
    assert board.hero_health == 38


def test_wrath_weaver_effect_1() -> None:
    """Test the Wrath Weaver minion effect when a Demon is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.WRATH_WEAVER)
    board.add_minion_to_hand(minions.IMP)

    board.play_minion(0)
    wrath_weaver = board.board[0]
    board.play_minion(1)
    # When a Demon is played, Wrath Weaver deals 1 damage to the hero, and gains +2/+2.
    assert board.hero_health == 39 and wrath_weaver.current_attack == 3 \
                                   and wrath_weaver.current_health == 5


def test_wrath_weaver_effect_2() -> None:
    """Test the Wrath Weaver minion effect when a non-Demon is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.WRATH_WEAVER)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)

    board.play_minion(0)
    wrath_weaver = board.board[0]
    board.play_minion(1)
    # When a Demon is played, Wrath Weaver deals 1 damage to the hero, and gains +2/+2.
    assert board.hero_health == 40 and wrath_weaver.current_attack == 1 \
                                   and wrath_weaver.current_health == 3


def test_golden_wrath_weaver_effect_1() -> None:
    """Test the golden Wrath Weaver minion effect when a Demon is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.WRATH_WEAVER_GOLDEN)
    board.add_minion_to_hand(minions.IMP)

    board.play_minion(0)
    wrath_weaver = board.board[0]
    board.play_minion(1)
    # When a Demon is played, Wrath Weaver deals 1 damage to the hero, and gains +2/+2.
    assert board.hero_health == 39 and wrath_weaver.current_attack == 6 \
                                   and wrath_weaver.current_health == 10


def test_golden_wrath_weaver_effect_2() -> None:
    """Test the golden Wrath Weaver minion effect when a non-Demon is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.WRATH_WEAVER_GOLDEN)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)

    board.play_minion(0)
    wrath_weaver = board.board[0]
    board.play_minion(1)
    # When a Demon is played, Wrath Weaver deals 1 damage to the hero, and gains +2/+2.
    assert board.hero_health == 40 and wrath_weaver.current_attack == 2 \
                                   and wrath_weaver.current_health == 6


def test_refreshing_anomaly_battlecry() -> None:
    """Test the battlecry effect for the Refreshing Anomaly minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.REFRESHING_ANOMALY)
    board.play_minion(0)

    board.next_turn()
    assert board.refresh_cost == 0
    board.refresh_recruits()  # This one is free thanks to the Refreshing Anomaly!
    assert board.refresh_cost == 1


def test_golden_refreshing_anomaly_battlecry() -> None:
    """Test the battlecry effect for the golden Refreshing Anomaly minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.REFRESHING_ANOMALY_GOLDEN)
    board.play_minion(0)

    board.next_turn()
    assert board.refresh_cost == 0
    board.refresh_recruits()  # This one is free thanks to the Refreshing Anomaly!
    assert board.refresh_cost == 0
    board.refresh_recruits()  # This one is free thanks to the Refreshing Anomaly!
    assert board.refresh_cost == 1


def test_sellemental_effect() -> None:
    """Test the effect for the Sellemental minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.play_minion(0)

    # When the Sellemental is sold, a Water Droplet is add to the hand.
    board.sell_minion(0)
    assert list(filter(lambda x: x is not None, board.hand)) == [minions.WATER_DROPLET]


def test_golden_sellemental_effect() -> None:
    """Test the effect for the golden Sellemental minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SELLEMENTAL_GOLDEN)
    board.play_minion(0)

    # When the golden Sellemental is sold, two Water Droplets are add to the hand.
    board.sell_minion(0)
    expected = [minions.WATER_DROPLET, minions.WATER_DROPLET]
    assert list(filter(lambda x: x is not None, board.hand)) == expected


def test_micro_machine_effect() -> None:
    """Test the effect for the Micro Machine minion."""
    board = TavernGameBoard()
    board.next_turn()
    board.add_minion_to_hand(minions.MICRO_MACHINE)
    board.play_minion(0)

    micro_machine = board.board[0]
    assert micro_machine.current_attack == 1
    for i in range(3):
        # At the start of each turn, we gain +1 Attack, but our health should not change.
        board.next_turn()
        assert micro_machine.current_attack == i + 2 and micro_machine.current_health == 2


def test_golden_micro_machine_effect() -> None:
    """Test the effect for the golden Micro Machine minion."""
    board = TavernGameBoard()
    board.next_turn()
    board.add_minion_to_hand(minions.MICRO_MACHINE_GOLDEN)
    board.play_minion(0)

    micro_machine = board.board[0]
    assert micro_machine.current_attack == 2
    for i in range(3):
        # At the start of each turn, we gain +2 Attack, but our health should not change.
        board.next_turn()
        assert micro_machine.current_attack == 2 * (i + 2) and micro_machine.current_health == 4


def test_micro_mummy_effect() -> None:
    """Test the effect for the Micro Mummy minion."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.MICRO_MUMMY)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.play_minion(0)
    board.play_minion(1)

    tabbycat = board.board[1]
    for i in range(3):
        # At the end of each turn, give a random friendly minion +1 Attack,
        # but the health should not change.
        assert tabbycat.current_attack == i + 1 and tabbycat.current_health == 1
        board.next_turn()
        assert tabbycat.current_attack == i + 2 and tabbycat.current_health == 1


def test_golden_micro_mummy_effect() -> None:
    """Test the effect for the golden Micro Mummy minion."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.MICRO_MUMMY_GOLDEN)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.play_minion(0)
    board.play_minion(1)

    tabbycat = board.board[1]
    for i in range(3):
        # At the end of each turn, give a random friendly minion +2 Attack,
        # but the health should not change.
        assert tabbycat.current_attack == 2 * i + 1 and tabbycat.current_health == 1
        board.next_turn()
        assert tabbycat.current_attack == 2 * (i + 1) + 1  and tabbycat.current_health == 1


def test_murloc_tidecaller_effect() -> None:
    """Test the effect for the Murloc Tidecaller minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.play_minion(0)

    # Whenever we summon a Murloc, the tidecaller minion gains +1 attack.
    board.summon_minion(minions.MURLOC_SCOUT)
    murloc_tidecaller = board.board[0]
    assert murloc_tidecaller.current_attack == 2


def test_golden_murloc_tidecaller_effect() -> None:
    """Test the effect for the golden Murloc Tidecaller minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER_GOLDEN)
    board.play_minion(0)

    # Whenever we summon a Murloc, the tidecaller minion gains +2 attack.
    board.summon_minion(minions.MURLOC_SCOUT)
    murloc_tidecaller = board.board[0]
    assert murloc_tidecaller.current_attack == 4


def test_murloc_tidehunter_battlecry() -> None:
    """Test the battlecry effect for the Murloc Tidehunter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER)
    board.play_minion(0)
    assert board.get_minions_on_board() == [minions.MURLOC_TIDEHUNTER, minions.MURLOC_SCOUT]


def test_golden_murloc_tidehunter_battlecry() -> None:
    """Test the battlecry effect for the golden Murloc Tidehunter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER_GOLDEN)
    board.play_minion(0)
    expected = [minions.MURLOC_TIDEHUNTER_GOLDEN, minions.MURLOC_SCOUT_GOLDEN]
    assert board.get_minions_on_board() == expected


def test_rockpool_hunter_battlecry() -> None:
    """Test the battlecry effect for the Rockpool Hunter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    murloc_scout = board.board[0]
    assert murloc_scout.current_attack == 1 and murloc_scout.current_health == 1

    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    board.play_minion(0)

    assert murloc_scout.current_attack == 2 and murloc_scout.current_health == 2


def test_golden_rockpool_hunter_battlecry() -> None:
    """Test the battlecry effect for the golden Rockpool Hunter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    murloc_scout = board.board[0]
    assert murloc_scout.current_attack == 1 and murloc_scout.current_health == 1

    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER_GOLDEN)
    board.play_minion(0)

    assert murloc_scout.current_attack == 3 and murloc_scout.current_health == 3


def test_deck_swabbie_battlecry() -> None:
    """Test the battlecry effect for the Deck Swabbie minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.DECK_SWABBIE)
    board.play_minion(0)

    # Tavern upgrade should now cost 4 gold.
    board.give_gold(4)
    board.upgrade_tavern()
    assert board.tavern_tier == 2 and board.gold == 0

    # Discount only applied once. The next upgrade should be full price (7 gold).
    board.give_gold(7)
    board.upgrade_tavern()
    assert board.tavern_tier == 3 and board.gold == 0


def test_golden_deck_swabbie_battlecry() -> None:
    """Test the battlecry effect for the golden Deck Swabbie minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.DECK_SWABBIE_GOLDEN)
    board.play_minion(0)

    # Tavern upgrade should now cost 3 gold.
    board.give_gold(3)
    board.upgrade_tavern()
    assert board.tavern_tier == 2 and board.gold == 0

    # Discount only applied once. The next upgrade should be full price (7 gold).
    board.give_gold(7)
    board.upgrade_tavern()
    assert board.tavern_tier == 3 and board.gold == 0


def test_pack_leader_effect_1() -> None:
    """Test the effect for the Pack Leader minion when a Beast is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PACK_LEADER)
    board.play_minion(0)

    board.summon_minion(minions.TABBYCAT)
    tabbycat = board.board[1]
    assert tabbycat.current_attack == 3 and tabbycat.current_health == 1


def test_pack_leader_effect_2() -> None:
    """Test the effect for the Pack Leader minion when a non-Beast is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PACK_LEADER)
    board.play_minion(0)

    board.summon_minion(minions.IMP)
    tabbycat = board.board[1]
    assert tabbycat.current_attack == 1 and tabbycat.current_health == 1


def test_golden_pack_leader_effect_1() -> None:
    """Test the effect for the golden Pack Leader minion when a Beast is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PACK_LEADER_GOLDEN)
    board.play_minion(0)

    board.summon_minion(minions.TABBYCAT)
    tabbycat = board.board[1]
    assert tabbycat.current_attack == 5 and tabbycat.current_health == 1


def test_golden_pack_leader_effect_2() -> None:
    """Test the effect for the golden Pack Leader minion when a non-Beast is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PACK_LEADER_GOLDEN)
    board.play_minion(0)

    board.summon_minion(minions.IMP)
    tabbycat = board.board[1]
    assert tabbycat.current_attack == 1 and tabbycat.current_health == 1


def test_rabid_saurolisk_effect_1() -> None:
    """Test the effect for the Rabid Saurolisk minion when a minion with Deathrattle is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK)
    board.play_minion(0)

    board.add_minion_to_hand(minions.KINDLY_GRANDMOTHER)
    board.play_minion(0)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 4 and rabid_saurolisk.current_health == 4


def test_rabid_saurolisk_effect_2() -> None:
    """Test the effect for the Rabid Saurolisk minion when a minion with Deathrattle is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK)
    board.play_minion(0)

    board.summon_minion(minions.KINDLY_GRANDMOTHER)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 3 and rabid_saurolisk.current_health == 2


def test_rabid_saurolisk_effect_2() -> None:
    """Test the effect for the Rabid Saurolisk minion when a minion without Deathrattle is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK)
    board.play_minion(0)

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 3 and rabid_saurolisk.current_health == 2


def test_golden_rabid_saurolisk_effect_1() -> None:
    """Test the effect for the golden Rabid Saurolisk minion when a minion with Deathrattle is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK_GOLDEN)
    board.play_minion(0)

    board.add_minion_to_hand(minions.KINDLY_GRANDMOTHER)
    board.play_minion(0)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 8 and rabid_saurolisk.current_health == 8


def test_golden_rabid_saurolisk_effect_2() -> None:
    """Test the effect for the Rabid Saurolisk minion when a minion with Deathrattle is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK_GOLDEN)
    board.play_minion(0)

    board.summon_minion(minions.KINDLY_GRANDMOTHER)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 6 and rabid_saurolisk.current_health == 4


def test_golden_rabid_saurolisk_effect_3() -> None:
    """Test the effect for the Rabid Saurolisk minion when a minion without Deathrattle is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.RABID_SAUROLISK_GOLDEN)
    board.play_minion(0)

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)

    rabid_saurolisk = board.board[0]
    assert rabid_saurolisk.current_attack == 6 and rabid_saurolisk.current_health == 4


def test_nathrezim_overseer_battlecry() -> None:
    """Test the battlecry effect for the Nathrezim Overseer minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.NATHREZIM_OVERSEER)
    board.play_minion(0)
    board.play_minion(1)

    imp = board.board[0]
    assert imp.current_attack == 3 and imp.current_health == 3


def test_golden_nathrezim_overseer_battlecry() -> None:
    """Test the battlecry effect for the Nathrezim Overseer minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.NATHREZIM_OVERSEER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    imp = board.board[0]
    assert imp.current_attack == 5 and imp.current_health == 5


def test_steward_of_time_effect() -> None:
    """Test the effect for the Steward of Time minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.STEWARD_OF_TIME)
    board.play_minion(0)

    # Add a few minions to the board
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.DRAGON_SPAWN_LIEUTENANT)
    board.add_minion_to_hand(minions.MICRO_MACHINE)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)

    # Sell minion
    # This gives every minion on board a +1/+1 buff.
    board.sell_minion(0)

    minion_a, minion_b, minion_c = board.get_minions_on_board()
    assert minion_a.current_attack == 2 and minion_a.current_health == 2
    assert minion_b.current_attack == 3 and minion_b.current_health == 4
    assert minion_c.current_attack == 2 and minion_c.current_health == 3


def test_golden_steward_of_time_effect() -> None:
    """Test the effect for the golden Steward of Time minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.STEWARD_OF_TIME_GOLDEN)
    board.play_minion(0)

    # Add a few minions to the board
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.DRAGON_SPAWN_LIEUTENANT)
    board.add_minion_to_hand(minions.MICRO_MACHINE)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)

    # Sell minion
    # This gives every minion on board a +2/+2 buff.
    board.sell_minion(0)

    minion_a, minion_b, minion_c = board.get_minions_on_board()
    assert minion_a.current_attack == 3 and minion_a.current_health == 3
    assert minion_b.current_attack == 4 and minion_b.current_health == 5
    assert minion_c.current_attack == 3 and minion_c.current_health == 4


def test_molten_rock_effect_1() -> None:
    """Test the effect for the Molten Rock minion when an Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK)
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.play_minion(0)
    board.play_minion(1)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 2 and molten_rock.current_health == 5


def test_molten_rock_effect_2() -> None:
    """Test the effect for the Molten Rock minion when a non-Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    board.play_minion(1)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 2 and molten_rock.current_health == 4


def test_molten_rock_effect_3() -> None:
    """Test the effect for the Molten Rock minion when an Elemental is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK)
    board.play_minion(0)

    board.summon_minion(minions.SELLEMENTAL)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 2 and molten_rock.current_health == 4


def test_golden_molten_rock_effect_1() -> None:
    """Test the effect for the golden Molten Rock minion when an Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK_GOLDEN)
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.play_minion(0)
    board.play_minion(1)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 4 and molten_rock.current_health == 10


def test_golden_molten_rock_effect_2() -> None:
    """Test the effect for the golden Molten Rock minion when a non-Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK_GOLDEN)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    board.play_minion(1)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 4 and molten_rock.current_health == 8


def test_golden_molten_rock_effect_3() -> None:
    """Test the effect for the golden Molten Rock minion when an Elemental is summoned."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MOLTEN_ROCK_GOLDEN)
    board.play_minion(0)

    board.summon_minion(minions.SELLEMENTAL)

    molten_rock = board.board[0]
    assert molten_rock.current_attack == 4 and molten_rock.current_health == 8


def test_party_elemental_effect_1() -> None:
    """Test the effect for the Party Elemental minion when an Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.play_minion(0)
    board.play_minion(1)

    party_elemental = board.board[0]
    assert party_elemental.current_attack == 4 and party_elemental.current_health == 3


def test_party_elemental_effect_2() -> None:
    """Test the effect for the Party Elemental minion when a non-Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    board.play_minion(1)

    party_elemental = board.board[0]
    assert party_elemental.current_attack == 3 and party_elemental.current_health == 2


def test_golden_party_elemental_effect_1() -> None:
    """Test the effect for the golden Party Elemental minion when an Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL_GOLDEN)
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.play_minion(0)
    board.play_minion(1)

    party_elemental = board.board[0]
    assert party_elemental.current_attack == 8 and party_elemental.current_health == 6


def test_golden_party_elemental_effect_2() -> None:
    """Test the effect for the golden Party Elemental minion when a non-Elemental is played."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL_GOLDEN)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)
    board.play_minion(1)

    party_elemental = board.board[0]
    assert party_elemental.current_attack == 6 and party_elemental.current_health == 4


def test_metaltooth_leaper_battlecry() -> None:
    """Test the battlecry effect for the Metaltooth Leaper minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.HARVEST_GOLEM)
    board.add_minion_to_hand(minions.KABOOM_BOT)
    board.add_minion_to_hand(minions.DAMAGED_GOLEM)
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)
    board.add_minion_to_hand(minions.METALTOOTH_LEAPER)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    minion_a, minion_b, minion_c, minion_d = board.get_minions_on_board()[:4]
    assert minion_a.current_attack == 4 and minion_a.current_health == 3
    assert minion_b.current_attack == 4 and minion_b.current_health == 2
    assert minion_c.current_attack == 4 and minion_c.current_health == 1
    assert minion_d.current_attack == 3 and minion_d.current_health == 2


def test_golden_metaltooth_leaper_battlecry() -> None:
    """Test the battlecry effect for the golden Metaltooth Leaper minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.HARVEST_GOLEM)
    board.add_minion_to_hand(minions.KABOOM_BOT)
    board.add_minion_to_hand(minions.DAMAGED_GOLEM)
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)
    board.add_minion_to_hand(minions.METALTOOTH_LEAPER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    minion_a, minion_b, minion_c, minion_d = board.get_minions_on_board()[:4]
    assert minion_a.current_attack == 6 and minion_a.current_health == 3
    assert minion_b.current_attack == 6 and minion_b.current_health == 2
    assert minion_c.current_attack == 6 and minion_c.current_health == 1
    assert minion_d.current_attack == 3 and minion_d.current_health == 2


def test_freedealing_gambler_effect() -> None:
    """Test the effect for the Freedealing Gambler minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.FREEDEALING_GAMBLER)
    board.play_minion(0)
    board.sell_minion(0)
    # The minion sells for 3 gold.
    assert board.gold == 3

def test_golden_freedealing_gambler_effect() -> None:
    """Test the effect for the golden Freedealing Gambler minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.FREEDEALING_GAMBLER_GOLDEN)
    board.play_minion(0)
    board.sell_minion(0)
    # The minion sells for 6 gold.
    assert board.gold == 6


def test_managerie_mug_battlecry_1() -> None:
    """Test the battlecry effect for the Managerie Mug minion when there are at least 3 friendly
    minions of different types.
    """
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)  # Elemental
    board.add_minion_to_hand(minions.MURLOC_SCOUT)  # Murloc
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)   # Murloc
    board.add_minion_to_hand(minions.TABBYCAT)  # Beast
    board.add_minion_to_hand(minions.MENAGERIE_MUG)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    random.seed(69)
    board.play_minion(4)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 4 and all_minions[0].current_health == 3
    assert all_minions[2].current_attack == 2 and all_minions[2].current_health == 3
    assert all_minions[3].current_attack == 2 and all_minions[3].current_health == 2


def test_managerie_mug_battlecry_2() -> None:
    """Test the battlecry effect for the Managerie Mug minion when there are less than 3 friendly
    minions of different types.
    """
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)  # Elemental
    board.add_minion_to_hand(minions.TABBYCAT)  # Beast
    board.add_minion_to_hand(minions.MENAGERIE_MUG)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)

    random.seed(69)
    board.play_minion(4)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 4 and all_minions[0].current_health == 3
    assert all_minions[1].current_attack == 2 and all_minions[1].current_health == 2


def test_golden_managerie_mug_battlecry_1() -> None:
    """Test the battlecry effect for the golden Managerie Mug minion when there are at
    least 3 friendly minions of different types.
    """
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)  # Elemental
    board.add_minion_to_hand(minions.MURLOC_SCOUT)  # Murloc
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)   # Murloc
    board.add_minion_to_hand(minions.TABBYCAT)  # Beast
    board.add_minion_to_hand(minions.MENAGERIE_MUG_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    random.seed(69)
    board.play_minion(4)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 5 and all_minions[0].current_health == 4
    assert all_minions[2].current_attack == 3 and all_minions[2].current_health == 4
    assert all_minions[3].current_attack == 3 and all_minions[3].current_health == 3


def test_golden_managerie_mug_battlecry_2() -> None:
    """Test the battlecry effect for the golden Managerie Mug minion when there are
    less than 3 friendly minions of different types.
    """
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.PARTY_ELEMENTAL)  # Elemental
    board.add_minion_to_hand(minions.TABBYCAT)  # Beast
    board.add_minion_to_hand(minions.MENAGERIE_MUG_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)

    random.seed(69)
    board.play_minion(4)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 5 and all_minions[0].current_health == 4
    assert all_minions[1].current_attack == 3 and all_minions[1].current_health == 3


def test_houndmaster_battlecry_1() -> None:
    """Test the battlecry effect for the Houndmaster minion when there is a friendly Beast."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.HOUNDMASTER)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 3 and minion.current_health == 3 \
                                      and minion.current_abilities == CardAbility.TAUNT


def test_houndmaster_battlecry_2() -> None:
    """Test the battlecry effect for the Houndmaster minion when there is no friendly Beast."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.HOUNDMASTER)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 1 and minion.current_health == 1 \
                                      and minion.current_abilities == CardAbility.NONE


def test_golden_houndmaster_battlecry_1() -> None:
    """Test the battlecry effect for the golden Houndmaster minion when there is a friendly Beast."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.HOUNDMASTER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 5 and minion.current_health == 5 \
                                      and minion.current_abilities == CardAbility.TAUNT


def test_golden_houndmaster_battlecry_2() -> None:
    """Test the battlecry effect for the golden Houndmaster minion when there is no friendly Beast."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.HOUNDMASTER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 1 and minion.current_health == 1 \
                                      and minion.current_abilities == CardAbility.NONE


def test_crystal_weaver_battlecry() -> None:
    """Test the battlecry effect for the Crystal Weaver minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.CRYSTAL_WEAVER)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 2 and all_minions[0].current_health == 2
    assert all_minions[1].current_attack == 3 and all_minions[1].current_health == 5
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 1
    assert all_minions[3].current_attack == 5 and all_minions[3].current_health == 4


def test_golden_crystal_weaver_battlecry() -> None:
    """Test the battlecry effect for the golden Crystal Weaver minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.CRYSTAL_WEAVER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.get_minions_on_board()
    assert all_minions[0].current_attack == 3 and all_minions[0].current_health == 3
    assert all_minions[1].current_attack == 4 and all_minions[1].current_health == 6
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 1
    assert all_minions[3].current_attack == 10 and all_minions[3].current_health == 8


def test_soul_devourer_battlecry_1() -> None:
    """Test the battlecry effect for the Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.SOUL_DEVOURER)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is None and minion.current_attack == 4 and minion.current_health == 4
    assert board.gold == 3


def test_soul_devourer_battlecry_2() -> None:
    """Test the battlecry effect for the Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.SOUL_DEVOURER)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is None and minion.current_attack == 5 and minion.current_health == 7
    assert board.gold == 3


def test_soul_devourer_battlecry_3() -> None:
    """Test the battlecry effect for the Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SOUL_DEVOURER)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    random.seed(69)
    board.play_minion(3)

    minion = board.board[3]
    assert board.board[0] is None and minion.current_attack == 5 and minion.current_health == 7
    assert board.board[1] is not None and board.board[2] is not None
    assert board.gold == 3


def test_soul_devourer_battlecry_4() -> None:
    """Test the battlecry effect for the Soul Devourer when there is no friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SOUL_DEVOURER)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is not None and minion.current_attack == 3 and minion.current_health == 3
    assert board.gold == 3


def test_golden_soul_devourer_battlecry_1() -> None:
    """Test the battlecry effect for the golden Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP)
    board.add_minion_to_hand(minions.SOUL_DEVOURER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is None and minion.current_attack == 8 and minion.current_health == 8
    assert board.gold == 6


def test_golden_soul_devourer_battlecry_2() -> None:
    """Test the battlecry effect for the golden Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.SOUL_DEVOURER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is None and minion.current_attack == 10 and minion.current_health == 14
    assert board.gold == 6


def test_golden_soul_devourer_battlecry_3() -> None:
    """Test the battlecry effect for the golden Soul Devourer when there is another friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.IMP_GANG_BOSS)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SOUL_DEVOURER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    random.seed(69)
    board.play_minion(3)

    minion = board.board[3]
    assert board.board[0] is None and minion.current_attack == 10 and minion.current_health == 14
    assert board.board[1] is not None and board.board[2] is not None
    assert board.gold == 6


def test_golden_soul_devourer_battlecry_4() -> None:
    """Test the battlecry effect for the golden Soul Devourer when there is no friendly Demon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SOUL_DEVOURER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[1]
    assert board.board[0] is not None and minion.current_attack == 6 and minion.current_health == 6
    assert board.gold == 6


def test_hangry_dragon_effect_1() -> None:
    """Test the effect for the Hangry Dragon minion."""
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.HANGRY_DRAGON)
    friendly_board.play_minion(0)

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.ALLEYCAT)
    enemy_board.play_minion(0)

    friendly_board.battle(enemy_board)
    friendly_board.next_turn()

    minion = friendly_board.board[0]
    assert minion.current_attack == 6 and minion.current_health == 6


def test_hangry_dragon_effect_2() -> None:
    """Test the effect for the Hangry Dragon minion."""
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.HANGRY_DRAGON)
    friendly_board.play_minion(0)

    enemy_board = TavernGameBoard()

    big_boi_murloc_scout = minions.MURLOC_SCOUT.clone()
    big_boi_murloc_scout.add_buff(Buff(10, 10, CardAbility.NONE))
    enemy_board.add_minion_to_hand(big_boi_murloc_scout, clone=False)
    enemy_board.play_minion(0)

    friendly_board.battle(enemy_board)
    friendly_board.next_turn()

    minion = friendly_board.board[0]
    assert minion.current_attack == 4 and minion.current_health == 4


def test_golden_hangry_dragon_effect_1() -> None:
    """Test the effect for the golden Hangry Dragon minion."""
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.HANGRY_DRAGON_GOLDEN)
    friendly_board.play_minion(0)

    enemy_board = TavernGameBoard()
    enemy_board.add_minion_to_hand(minions.ALLEYCAT)
    enemy_board.play_minion(0)

    friendly_board.battle(enemy_board)
    friendly_board.next_turn()

    minion = friendly_board.board[0]
    assert minion.current_attack == 12 and minion.current_health == 12


def test_golden_hangry_dragon_effect_2() -> None:
    """Test the effect for the golden Hangry Dragon minion."""
    friendly_board = TavernGameBoard()
    friendly_board.add_minion_to_hand(minions.HANGRY_DRAGON_GOLDEN)
    friendly_board.play_minion(0)

    enemy_board = TavernGameBoard()

    big_boi_murloc_scout = minions.MURLOC_SCOUT.clone()
    big_boi_murloc_scout.add_buff(Buff(10, 10, CardAbility.NONE))
    enemy_board.add_minion_to_hand(big_boi_murloc_scout, clone=False)
    enemy_board.play_minion(0)

    friendly_board.battle(enemy_board)
    friendly_board.next_turn()

    minion = friendly_board.board[0]
    assert minion.current_attack == 8 and minion.current_health == 8


def test_twilight_emissary_battlecry_1() -> None:
    """Test the battlecry effect for the Twilight Emissary minion when there is a friendly Dragon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.HANGRY_DRAGON)
    board.add_minion_to_hand(minions.TWILIGHT_EMISSARY)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 6 and minion.current_health == 6


def test_twilight_emissary_battlecry_2() -> None:
    """Test the battlecry effect for the Twilight Emissary minion when there isn't a friendly Dragon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.TWILIGHT_EMISSARY)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 1 and minion.current_health == 1


def test_golden_twilight_emissary_battlecry_1() -> None:
    """Test the battlecry effect for the golden Twilight Emissary minion when there is a friendly Dragon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.HANGRY_DRAGON)
    board.add_minion_to_hand(minions.TWILIGHT_EMISSARY_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 8 and minion.current_health == 8


def test_golden_twilight_emissary_battlecry_2() -> None:
    """Test the battlecry effect for the golden Twilight Emissary minion when there isn't a friendly Dragon."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.TWILIGHT_EMISSARY_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion = board.board[0]
    assert minion.current_attack == 1 and minion.current_health == 1


def test_arcane_assistant_battlecry() -> None:
    """Test the battlecry effect for the Arcane Assistant minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.add_minion_to_hand(minions.WATER_DROPLET)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ARCANE_ASSISTANT)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.board
    assert all_minions[0].current_attack == 3 and all_minions[0].current_health == 3
    assert all_minions[1].current_attack == 3 and all_minions[1].current_health == 3
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 1
    assert all_minions[3].current_attack == 3 and all_minions[3].current_health == 3


def test_golden_arcane_assistant_battlecry() -> None:
    """Test the battlecry effect for the golden Arcane Assistant minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SELLEMENTAL)
    board.add_minion_to_hand(minions.WATER_DROPLET)
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ARCANE_ASSISTANT_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.board
    assert all_minions[0].current_attack == 4 and all_minions[0].current_health == 4
    assert all_minions[1].current_attack == 4 and all_minions[1].current_health == 4
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 1
    assert all_minions[3].current_attack == 6 and all_minions[3].current_health == 6


def test_iron_sensei_effect_1() -> None:
    """Test the effect for the Iron Sensei minion when there is a friendly Mech on the board."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.DEFLECT_O_BOT)
    board.add_minion_to_hand(minions.IRON_SENSEI)
    board.play_minion(0)
    board.play_minion(1)
    board.next_turn()

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 5 and minion_a.current_health == 4
    assert minion_b.current_attack == 2 and minion_b.current_health == 2


def test_iron_sensei_effect_2() -> None:
    """Test the effect for the Iron Sensei minion when there is no friendly Mech on the board."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.IRON_SENSEI)
    board.play_minion(0)
    board.play_minion(1)
    board.next_turn()

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 1 and minion_a.current_health == 1
    assert minion_b.current_attack == 2 and minion_b.current_health == 2


def test_golden_iron_sensei_effect_1() -> None:
    """Test the effect for the golden Iron Sensei minion when there is a friendly Mech on the board."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.DEFLECT_O_BOT)
    board.add_minion_to_hand(minions.IRON_SENSEI_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.next_turn()

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 7 and minion_a.current_health == 6
    assert minion_b.current_attack == 4 and minion_b.current_health == 4


def test_golden_iron_sensei_effect_2() -> None:
    """Test the effect for the golden Iron Sensei minion when there is no friendly Mech on the board."""
    board = TavernGameBoard()
    board.next_turn()

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.IRON_SENSEI_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.next_turn()

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 1 and minion_a.current_health == 1
    assert minion_b.current_attack == 4 and minion_b.current_health == 4


def test_screwjank_clunker_battlecry_1() -> None:
    """Test the battlecry effect for the Screwjank Clunker minion when there is a friendly Mechc on the board."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.DEFLECT_O_BOT)
    board.add_minion_to_hand(minions.SCREWJANK_CLUNKER)
    board.play_minion(0)
    board.play_minion(1)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 5 and minion_a.current_health == 4
    assert minion_b.current_attack == 2 and minion_b.current_health == 5


def test_screwjank_clunker_battlecry_2() -> None:
    """Test the battlecry effect for the Screwjank Clunker minion when there is no friendly Mechc on the board."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SCREWJANK_CLUNKER)
    board.play_minion(0)
    board.play_minion(1)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 1 and minion_a.current_health == 1
    assert minion_b.current_attack == 2 and minion_b.current_health == 5


def test_golden_screwjank_clunker_battlecry_1() -> None:
    """Test the battlecry effect for the golden Screwjank Clunker minion when there is a friendly Mechc on the board."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.DEFLECT_O_BOT)
    board.add_minion_to_hand(minions.SCREWJANK_CLUNKER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 7 and minion_a.current_health == 6
    assert minion_b.current_attack == 4 and minion_b.current_health == 10


def test_golden_screwjank_clunker_battlecry_2() -> None:
    """Test the battlecry effect for the golden Screwjank Clunker minion when there is no friendly Mechc on the board."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.SCREWJANK_CLUNKER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 1 and minion_a.current_health == 1
    assert minion_b.current_attack == 4 and minion_b.current_health == 10


def test_coldlight_seer_battlecry() -> None:
    """Test the battlecry effect for the Coldlight Seer minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.COLDLIGHT_SEER)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    all_minions = board.board
    assert all_minions[0].current_attack == 2 and all_minions[0].current_health == 4
    assert all_minions[1].current_attack == 2 and all_minions[1].current_health == 5
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 4
    assert all_minions[3].current_attack == 1 and all_minions[3].current_health == 1
    assert all_minions[4].current_attack == 2 and all_minions[4].current_health == 3


def test_golden_coldlight_seer_battlecry() -> None:
    """Test the battlecry effect for the golden Coldlight Seer minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.COLDLIGHT_SEER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    all_minions = board.board
    assert all_minions[0].current_attack == 2 and all_minions[0].current_health == 6
    assert all_minions[1].current_attack == 2 and all_minions[1].current_health == 7
    assert all_minions[2].current_attack == 1 and all_minions[2].current_health == 6
    assert all_minions[3].current_attack == 1 and all_minions[3].current_health == 1
    assert all_minions[4].current_attack == 4 and all_minions[4].current_health == 6


def test_felfin_navigator_battlecry() -> None:
    """Test the battlecry effect for the Felfin Navigator."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.FELFIN_NAVIGATOR)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    all_minions = board.board
    assert all_minions[0].current_attack == 3 and all_minions[0].current_health == 3
    assert all_minions[1].current_attack == 3 and all_minions[1].current_health == 4
    assert all_minions[2].current_attack == 2 and all_minions[2].current_health == 3
    assert all_minions[3].current_attack == 1 and all_minions[3].current_health == 1
    assert all_minions[4].current_attack == 4 and all_minions[4].current_health == 4


def test_golden_felfin_navigator_battlecry() -> None:
    """Test the battlecry effect for the golden Felfin Navigator minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.ROCKPOOL_HUNTER)
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.add_minion_to_hand(minions.TABBYCAT)
    board.add_minion_to_hand(minions.FELFIN_NAVIGATOR_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)
    board.play_minion(4)

    all_minions = board.board
    assert all_minions[0].current_attack == 4 and all_minions[0].current_health == 4
    assert all_minions[1].current_attack == 4 and all_minions[1].current_health == 5
    assert all_minions[2].current_attack == 3 and all_minions[2].current_health == 4
    assert all_minions[3].current_attack == 1 and all_minions[3].current_health == 1
    assert all_minions[4].current_attack == 8 and all_minions[4].current_health == 8


def test_bloodsail_cannoneer_battlecry() -> None:
    """Test the Bloodsail Cannoneer minion."""
    board =  TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.GOLDGRUBBER)
    board.add_minion_to_hand(minions.RIPSNARL_CAPTAIN)
    board.add_minion_to_hand(minions.BLOODSAIL_CANNONEER)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.board
    assert all_minions[0].current_attack == 1 and all_minions[0].current_health == 1
    assert all_minions[1].current_attack == 5 and all_minions[1].current_health == 2
    assert all_minions[2].current_attack == 7 and all_minions[2].current_health == 5
    assert all_minions[3].current_attack == 4 and all_minions[3].current_health == 3


def test_golden_bloodsail_cannoneer_battlecry() -> None:
    """Test the golden Bloodsail Cannoneer minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.add_minion_to_hand(minions.GOLDGRUBBER)
    board.add_minion_to_hand(minions.RIPSNARL_CAPTAIN)
    board.add_minion_to_hand(minions.BLOODSAIL_CANNONEER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)
    board.play_minion(2)
    board.play_minion(3)

    all_minions = board.board
    assert all_minions[0].current_attack == 1 and all_minions[0].current_health == 1
    assert all_minions[1].current_attack == 8 and all_minions[1].current_health == 2
    assert all_minions[2].current_attack == 10 and all_minions[2].current_health == 5
    assert all_minions[3].current_attack == 8 and all_minions[3].current_health == 6


def test_salty_looter_effect() -> None:
    """Test the effect for the Salty Looter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SALTY_LOOTER)
    board.play_minion(0)

    minion_a = board.board[0]
    assert minion_a.current_attack == 4 and minion_a.current_health == 4

    board.add_minion_to_hand(minions.GOLDGRUBBER)
    board.play_minion(0)

    minion_b = board.board[1]
    assert minion_a.current_attack == 5 and minion_a.current_health == 5
    assert minion_b.current_attack == 2 and minion_b.current_health == 2

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)

    minion_c = board.board[2]
    assert minion_a.current_attack == 5 and minion_a.current_health == 5
    assert minion_b.current_attack == 2 and minion_b.current_health == 2
    assert minion_c.current_attack == 1 and minion_c.current_health == 1


def test_golden_salty_looter_effect() -> None:
    """Test the effect for the golden Salty Looter minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.SALTY_LOOTER_GOLDEN)
    board.play_minion(0)

    minion_a = board.board[0]
    assert minion_a.current_attack == 8 and minion_a.current_health == 8

    board.add_minion_to_hand(minions.GOLDGRUBBER)
    board.play_minion(0)

    minion_b = board.board[1]
    assert minion_a.current_attack == 10 and minion_a.current_health == 10
    assert minion_b.current_attack == 2 and minion_b.current_health == 2

    board.add_minion_to_hand(minions.MURLOC_SCOUT)
    board.play_minion(0)

    minion_c = board.board[2]
    assert minion_a.current_attack == 10 and minion_a.current_health == 10
    assert minion_b.current_attack == 2 and minion_b.current_health == 2
    assert minion_c.current_attack == 1 and minion_c.current_health == 1


def test_southsea_strongarm_battlecry_1() -> None:
    """Test the battlecry effect for the Southsea Strongarm minion."""
    board = TavernGameBoard()
    board.give_gold(10)
    board._recruits = [
        minions.GOLDGRUBBER.clone(),
        minions.GOLDGRUBBER.clone(),
        minions.RIPSNARL_CAPTAIN.clone(),
        minions.MURLOC_SCOUT.clone(),
        minions.SOUTHSEA_STRONGARM.clone(),
        None
    ]

    board.buy_minion(0)
    board.buy_minion(1)
    board.buy_minion(2)

    board.give_gold(10)
    board.buy_minion(3)
    board.buy_minion(4)

    board.play_minion(0)
    board.play_minion(4)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 5 and minion_a.current_health == 5
    assert minion_b.current_attack == 4 and minion_b.current_health == 3


def test_southsea_strongarm_battlecry_2() -> None:
    """Test the battlecry effect for the Southsea Strongarm minion."""
    board = TavernGameBoard()
    board.give_gold(10)
    board._recruits = [
        minions.GOLDGRUBBER.clone(),
        minions.GOLDGRUBBER.clone(),
        minions.RIPSNARL_CAPTAIN.clone(),
        minions.MURLOC_SCOUT.clone(),
        minions.SOUTHSEA_STRONGARM.clone(),
        None
    ]

    board.buy_minion(0)
    board.buy_minion(1)
    board.buy_minion(2)

    board.give_gold(10)
    board.buy_minion(3)

    board.buy_minion(4)
    board.play_minion(4)

    minion = board.board[0]
    assert minion.current_attack == 4 and minion.current_health == 3


def test_golden_southsea_strongarm_battlecry_1() -> None:
    """Test the battlecry effect for the golden Southsea Strongarm minion."""
    board = TavernGameBoard()
    board.give_gold(10)
    board._recruits = [
        minions.GOLDGRUBBER.clone(),
        minions.GOLDGRUBBER.clone(),
        minions.RIPSNARL_CAPTAIN.clone(),
        minions.MURLOC_SCOUT.clone(),
        minions.SOUTHSEA_STRONGARM_GOLDEN.clone(),
        None
    ]

    board.buy_minion(0)
    board.buy_minion(1)
    board.buy_minion(2)

    board.give_gold(10)
    board.buy_minion(3)
    board.buy_minion(4)

    board.play_minion(0)
    board.play_minion(4)

    minion_a, minion_b = board.board[:2]
    assert minion_a.current_attack == 8 and minion_a.current_health == 8
    assert minion_b.current_attack == 8 and minion_b.current_health == 6


def test_golden_southsea_strongarm_battlecry_2() -> None:
    """Test the battlecry effect for the golden Southsea Strongarm minion."""
    board = TavernGameBoard()
    board.give_gold(10)
    board._recruits = [
        minions.GOLDGRUBBER.clone(),
        minions.GOLDGRUBBER.clone(),
        minions.RIPSNARL_CAPTAIN.clone(),
        minions.MURLOC_SCOUT.clone(),
        minions.SOUTHSEA_STRONGARM_GOLDEN.clone(),
        None
    ]

    board.buy_minion(0)
    board.buy_minion(1)
    board.buy_minion(2)

    board.give_gold(10)
    board.buy_minion(3)

    board.buy_minion(4)
    board.play_minion(4)

    minion = board.board[0]
    assert minion.current_attack == 8 and minion.current_health == 6


def test_khadgar_effect() -> None:
    """Test the effect for the Khadgar minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.KHADGAR)
    board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER)
    board.play_minion(0)
    board.play_minion(1)

    expected = [
        minions.KHADGAR, minions.MURLOC_TIDEHUNTER,
        minions.MURLOC_SCOUT, minions.MURLOC_SCOUT
    ]
    assert board.get_minions_on_board() == expected


def test_golden_khadgar_effect() -> None:
    """Test the effect for the Khadgar minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.KHADGAR_GOLDEN)
    board.add_minion_to_hand(minions.MURLOC_TIDEHUNTER_GOLDEN)
    board.play_minion(0)
    board.play_minion(1)

    expected = [
        minions.KHADGAR_GOLDEN, minions.MURLOC_TIDEHUNTER_GOLDEN,
        minions.MURLOC_SCOUT_GOLDEN, minions.MURLOC_SCOUT_GOLDEN,
        minions.MURLOC_SCOUT_GOLDEN
    ]
    assert board.get_minions_on_board() == expected
