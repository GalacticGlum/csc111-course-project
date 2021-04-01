"""Test the minion implementations."""
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


def test_murloc_tidecaller() -> None:
    """Test the effect for the Murloc Tidecaller minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.MURLOC_TIDECALLER)
    board.play_minion(0)

    # Whenever we summon a Murloc, the tidecaller minion gains +1 attack.
    board.summon_minion(minions.MURLOC_SCOUT)
    murloc_tidecaller = board.board[0]
    assert murloc_tidecaller.current_attack == 2


def test_golden_murloc_tidecaller() -> None:
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

