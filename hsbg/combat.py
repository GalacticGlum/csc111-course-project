"""A simulator of the combat phase in Hearthstone Battlegrounds."""
from __future__ import annotations
import re
import platform
import tempfile
import subprocess
from dataclasses import dataclass

from typing import Union
from pathlib import Path

from hsbg.models import CardAbility


# The default path of the C++ hsbg simulator binary file relative to the root directory.
INSTANCE_PATH = Path(__file__).parent.parent / 'instance'
INSTANCE_PATH.mkdir(exist_ok=True, parents=True)
try:
    if (INSTANCE_PATH / 'hsbg').is_file():
        _DEFAULT_HSBG_SIM_PATH = INSTANCE_PATH / 'hsbg'
    else:
        _DEFAULT_HSBG_SIM_PATH = list(INSTANCE_PATH.glob('hsbg.*'))[0]
except:
    raise ValueError('Could not find the C++ hsbg simulator binary file in the instance folder!')


# A list of abilities supported by the C++ simulator
SIMULATOR_ABILITIES = [
    CardAbility.TAUNT,
    CardAbility.DIVINE_SHIELD,
    CardAbility.POISONOUS,
    CardAbility.WINDFURY,
    CardAbility.REBORN
]


@dataclass
class Battle:
    """The result of the combat phase simulator.

    Instance Attributes:
        - win_probability: The probability of winning this battle.
        - tie_probability: The probability of a tie.
        - lose_probability: The probability of losing this battle.
        - mean_score: The mean score across all simulations of the battle.
        - median_score: The median score across all simulations of the battle.
        - mean_damage_taken: The mean damage taken (by the friendly hero) across all simulations of the battle.
        - mean_damage_dealt: The mean damage dealt (to the enemy hero) across all simulations of the battle.
        - expected_hero_health: The expected health of the hero after this battle.
        - expected_enemy_hero_health: The expected health of the enemy hero after this battle.
        - death_probability: The probability of the hero dying after this battle.
        - enemy_death_probability: The probability of the enemy hero dying after this battle.

    Representation Invariants:
        - 0 <= self.win_probability <= 1
        - 0 <= self.tie_probability <= 1
        - 0 <= self.lose_probability <= 1
        - self.win_probability + self.tie_probability + self.lose_probability == 1
        - 0 <= self.death_probability <= 1
        - 0 <= self.enemy_death_probability <= 1
    """
    win_probability: float
    tie_probability: float
    lose_probability: float
    mean_score: float
    median_score: float
    mean_damage_taken: float
    mean_damage_dealt: float
    expected_hero_health: float
    expected_enemy_hero_health: float
    death_probability: float
    enemy_death_probability: float

    def invert(self) -> Battle:
        """Return a new Battle where the friendly and enemy players are swapped."""
        return Battle(self.lose_probability, self.tie_probability, self.win_probability,
                      -self.mean_score, -self.median_score,
                      self.mean_damage_dealt, self.mean_damage_taken,
                      self.expected_enemy_hero_health, self.expected_hero_health,
                      self.enemy_death_probability, self.death_probability)

    @staticmethod
    def parse_simulator_output(output: str) -> Battle:
        """Return the Battle representing a string-based representation of the battle result.
        The output argument should match the output format of the C++ simulator.

        >>> output = '''
        ... --------------------------------
        ... win: 76.9%, tie: 0.0%, lose: 23.1%
        ... mean score: 11.875, median score: -16
        ... percentiles: -12 -10 -3 16 16 16 16 20 20 20 20
        ... mean damage taken: 1.764
        ... your expected health afterwards: 29.236, 3.14% chance to die
        ... mean damage dealt: 14.408
        ... their expected health afterwards: 10.592, 5.2% chance to die
        ... --------------------------------'''
        >>> expected = Battle(0.769, 0, 0.231, 11.875, -16, 1.764, 14.408,\
                              29.236, 10.592, 0.0314, 0.052)
        >>> expected == Battle.parse_simulator_output(output)
        True
        """
        def _get_field(name: str, value_suffix: str = '') -> float:
            """Return the value of a field in the simulator output string.
            Raise a ValueError if it could not be found.

            Note: A field is substring of the form: "<name>: <float>"

            Args:
                name: The name of the field.
                value_suffix: A suffix after the numerical value (e.g. '%' or '$')
                              to include while matching.
            """
            # Matches for "<name>: <float><value_suffix>"
            pattern = r'(?<={}:\s)-?\d+.?\d*{}'.format(name, value_suffix)
            match = re.search(pattern, output)
            if match is None:
                raise ValueError(f'Could not parse field with name \'{name}\' in:\n{output}')
            return float(match.group(0).replace(value_suffix, '').strip())

        def _get_death_probability(kind: str) -> float:
            """Return the probability of death for the given hero.
            Raise a ValueError if it could not be found.

            Preconditions:
                - kind in {'friendly', 'enemy'}
            """
            if kind == 'friendly':
                pattern = r'(?<=your expected health afterwards: ).*(?=% chance to die)'
            else:
                pattern = r'(?<=their expected health afterwards: ).*(?=% chance to die)'

            match = re.search(pattern, output)
            if match is None:
                raise ValueError(f'Could not find death probability for {kind} hero in:\n{output}.')

            parts = match.group(0).split(',')
            probability = parts[1].strip()
            probability = round(float(probability) / 100, len(probability) + 1)
            return probability

        # Get win, tie, and lose probabilities
        win_probability = _get_field('win', value_suffix='%') / 100
        tie_probability = _get_field('tie', value_suffix='%') / 100
        lose_probability = _get_field('lose', value_suffix='%') / 100

        # Get score stats
        mean_score = _get_field('mean score')
        median_score = _get_field('median score')

        # Get damage stats
        mean_damage_taken = _get_field('mean damage taken')
        mean_damage_dealt = _get_field('mean damage dealt')
        expected_hero_health = _get_field('your expected health afterwards')
        expected_enemy_hero_health = _get_field('their expected health afterwards')

        # Get death probabilities
        death_probability = _get_death_probability('friendly')
        enemy_death_probability = _get_death_probability('enemy')

        return Battle(win_probability, tie_probability, lose_probability,
                      mean_score, median_score, mean_damage_taken, mean_damage_dealt,
                      expected_hero_health, expected_enemy_hero_health,
                      death_probability, enemy_death_probability)


def simulate_combat(friendly_board: TavernGameBoard, enemy_board: TavernGameBoard, n: int = 1000) \
        -> Battle:
    """Simulate a battle between the given friendly and enemy boards.
    Return a Battle object containing match statistics averaged over all the runs.

    Args:
        friendly_board: The state of the friendly player's board.
        enemy_board: The state of the enemy player's board.
        n: The number of times to simulate the battle.
    """
    battle_config = battle_to_str(friendly_board, enemy_board)
    # Add run command
    battle_config += f'\nrun {n}'
    return run_hsbg_simulator(battle_config)


def run_hsbg_simulator(battle_config: str, bin_path: Union[Path, str] = _DEFAULT_HSBG_SIM_PATH) \
        -> Battle:
    """Invoke the C++ Hearthstone Battlegrounds simulator on the given battle configuration.
    Note: this function creates a temporary file to store the battle configuration.

    Args:
        battle_config: A series of commands that define the friendly and enemy board states.
        bin_path: The path to the binary file of the C++ simulator.
    """
    # Create temp file.
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False,
                                     dir=str(INSTANCE_PATH.absolute())) as temp_file:
        temp_file.write(battle_config)

    command = f'{bin_path} {temp_file.name}'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = map(lambda x: x.decode(), process.communicate())
    # Remove the temp file
    Path(temp_file.name).unlink()
    # Check for errors
    errors = list(re.finditer(r'(?<=Error:\s).*', stdout))
    if len(errors) > 0:
        padding = ' ' * len('ValueError: ')
        sim_errors = '\n'.join([f'{padding} - {error.group(0)}' for error in errors])
        raise ValueError(
            f'Invalid battle config. '
            f'Encountered {len(errors)} errors while parsing battle config.\n{sim_errors}'
        )
    else:
        return Battle.parse_simulator_output(stdout)


def battle_to_str(friendly_board: TavernGameBoard, enemy_board: TavernGameBoard) -> str:
    """Return the series of simulator commands that define the given battle."""
    return 'Board\n{}\nVS\n{}'.format(
        game_board_to_str(friendly_board),
        game_board_to_str(enemy_board)
    )


def game_board_to_str(board: TavernGameBoard) -> str:
    """Return the string representation of this TavernGameBoard.

    >>> from hsbg import TavernGameBoard
    >>> board = TavernGameBoard()
    >>> minions = [board.pool.find(name='Alleycat', is_golden=True),
    ...            board.pool.find(name='Murloc Scout'),
    ...            board.pool.find(name='Rockpool Hunter')]
    >>> all(board.add_minion_to_hand(minion) for minion in minions)
    True
    >>> all(board.play_minion(i) for i in range(len(minions)))
    True
    >>> print(game_board_to_str(board))
    level 1
    health 40
    * 2/2 golden Alleycat
    * 2/2 golden Tabbycat
    * 2/2 Murloc Scout
    * 2/3 Rockpool Hunter
    >>> coldlight_seer = board.pool.find(name='Coldlight Seer', is_golden=True)
    >>> board.add_minion_to_hand(coldlight_seer) and board.play_minion(0)
    True
    >>> print(game_board_to_str(board))
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
    >>> print(game_board_to_str(board))
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
            ability.as_format_str().lower() for ability in SIMULATOR_ABILITIES
            if ability in minion.current_abilities
        ]

        name = ('golden ' if minion.is_golden else '') + minion.name
        name_and_buffs = ', '.join([name] + buffs)
        line = f'* {minion.current_attack}/{minion.current_health} {name_and_buffs}'
        lines.append(line)

    return '\n'.join(lines)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
