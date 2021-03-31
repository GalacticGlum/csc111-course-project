"""Interface for the C++ combat phase simulator."""
from __future__ import annotations
import platform
import tempfile
import subprocess
from dataclasses import dataclass

from typing import Union
from pathlib import Path

from hsbg.models import CardAbility


# The default path of the C++ hsbg simulator binary file relative to the root directory.
if platform.system() == 'Windows':
    _DEFAULT_HSBG_SIM_PATH = Path(__file__).parent.parent / 'instance/hsbg.exe'
else:
    _DEFAULT_HSBG_SIM_PATH = Path(__file__).parent.parent / 'instance/hsbg'


# A list of abilities supported by the C++ simulator
_SIMULATOR_ABILITIES = [
    CardAbility.TAUNT,
    CardAbility.DIVINE_SHIELD,
    CardAbility.POISONOUS,
    CardAbility.WINDFURY
]

# A dict mapping CardAbility objects
CARD_ABILITY_TO_STR = {
    CardAbility.TAUNT: 'taunt',
    CardAbility.DIVINE_SHIELD: 'divine shield',
    CardAbility.POISONOUS: 'poisonous',
    CardAbility.WINDFURY: 'windfury'
}


@dataclass
class CombatPhaseResult:
    """The result of the combat phase simulator.

    Instance Attributes:
        - win_probability: The probability of the friendly player winning.
        - tie_probability: The probability of a tie.
        - lose_probability: The probability of the friendly player losing.
        - mean_score: The mean score across
        """


def run_hsbg_simulator(board_config: str, bin_path: Union[Path, str] = _DEFAULT_HSBG_SIM_PATH) \
        -> None:
    """Invoke the C++ Hearthstone Battlegrounds simulator on the given board configuration.
    Note: this function creates a temporary file to store the board configuration.

    Args:
        board_config: A series of commands that define the board state.
        bin_path: The path to the C++ simulator binary.
    """
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
        temp_file.write(board_config)

    command = f'{bin_path} {temp_file.name}'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = map(lambda x: x.decode(), process.communicate())
    # Remove the temp file
    Path(temp_file.name).unlink()
    return stdout


def _make_board_minion_state(board: TavernGameBoard) -> str:
    """Return the minions on given the board in a string format.

    >>> from hsbg import TavernGameBoard
    >>> board = TavernGameBoard()
    >>> minions = [board.pool.find(name='Alleycat', is_golden=True),
    ...            board.pool.find(name='Murloc Scout'),
    ...            board.pool.find(name='Rockpool Hunter')]
    >>> all(board.add_minion_to_hand(minion) for minion in minions)
    True
    >>> all(board.play_minion(i) for i in range(len(minions)))
    True
    >>> print(_make_board_minion_state(board))
    level 1
    health 40
    * 2/2 golden Alleycat
    * 2/2 golden Tabbycat
    * 2/2 Murloc Scout
    * 2/3 Rockpool Hunter
    >>> coldlight_seer = board.pool.find(name='Coldlight Seer', is_golden=True)
    >>> board.add_minion_to_hand(coldlight_seer) and board.play_minion(0)
    True
    >>> print(_make_board_minion_state(board))
    level 1
    health 40
    * 2/2 golden Alleycat
    * 2/2 golden Tabbycat
    * 2/6 Murloc Scout
    * 2/7 Rockpool Hunter
    * 4/6 golden Coldlight Seer
    >>> from hsbg.models import Buff, CardAbility
    >>> board.board[4].add_buff(Buff(1, 0, CardAbility.TAUNT | CardAbility.DIVINE_SHIELD))
    >>> board.give_gold(10)
    >>> board.upgrade_tavern()
    True
    >>> print(_make_board_minion_state(board))
    level 2
    health 40
    * 2/2 golden Alleycat
    * 2/2 golden Tabbycat
    * 2/6 Murloc Scout
    * 2/7 Rockpool Hunter
    * 5/6 golden Coldlight Seer, taunt, divine shield
    """
    lines = [
        f'level {board.tavern_tier}',
        f'health {board.hero_health}',
    ]

    for minion in board.board:
        if minion is None:
            continue

        buffs = [
            CARD_ABILITY_TO_STR[ability] for ability in _SIMULATOR_ABILITIES
            if ability in minion.current_abilities
        ]

        name = ('golden ' if minion.is_golden else '') + minion.name
        name_and_buffs = ', '.join([name] + buffs)
        line = f'* {minion.current_attack}/{minion.current_health} {name_and_buffs}'
        lines.append(line)

    return '\n'.join(lines)


def _make_config_from_board(friendly_board: TavernGameBoard, enemy_board: TavernGameBoard) -> str:
    """Return the series of simulator commands that define the given board state."""
    return 'Board\n{}\nVS\n{}'.format(
        _make_board_minion_state(friendly_board),
        _make_board_minion_state(enemy_board)
    )


def simulate_combat(board: TavernGameBoard) -> None:
    """Run the combat phase simulator on the given game board."""
    raise NotImplementedError


if __name__ == '__main__':
    import doctest
    doctest.testmod()
