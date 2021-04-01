"""Test the minion implementations."""
from hsbg import TavernGameBoard, minions


def test_alleycat_battlecry() -> None:
    """Test the battlecry for the Alleycat minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.ALLEYCAT)
    board.play_minion(0)
    assert board.get_minions_on_board() == [minions.ALLEYCAT, minions.TABBYCAT]


def test_alleycat_golden_battlecry() -> None:
    """Test the battlecry for the golden Alleycat minion."""
    board = TavernGameBoard()
    board.add_minion_to_hand(minions.ALLEYCAT_GOLDEN)
    board.play_minion(0)
    assert board.get_minions_on_board() == [minions.ALLEYCAT_GOLDEN, minions.TABBYCAT_GOLDEN]