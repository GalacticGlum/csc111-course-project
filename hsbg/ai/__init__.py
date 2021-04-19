"""Framework for making Hearthstone Battlegrounds AI.
This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
from __future__ import annotations
import json
import copy
from pathlib import Path
from typing import Tuple, List, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from hsbg import BattlegroundsGame
from hsbg.ai.players import Player


def run_games(n: int, players: List[Player], show_stats: bool = True, friendly_player: int = 0,
             n_jobs: int = 1, use_thread_pool: bool = False, copy_players: bool = True) -> List[int]:
    """Run n games using the given Players. Return a list with n elements, where the i-th element
    gives the zero-based index of the winning player for game i.

    Args:
        n: The number of games to run.
        players: A list of players to run the games with.
        show_stats: Whether to display summary statistics about the games.
        friendly_player: The index of the friendly player.
        n_jobs: The number of games to run in parallel.
        use_thread_pool: Whether to use the thread pool executor.
        copy_players: Whether to create a deepcopy of the players for every new game.

    Preconditions:
        - n >= 1
        - len(players) > 0 and len(players) % 2 == 0
        - n_jobs >= 1
    """
    stats = {i: 0 for i in range(len(players))}
    results = [None] * n

    def _game_done(winner: int) -> None:
        """..."""
        stats[winner] += 1
        results[game_index] = winner
        print(f'Game {game_index + 1} winner: Player {winner + 1}')

    def _get_players() -> List[Player]:
        """Return a list of players for a game.
        Copies players if copy_players is True.
        """
        return copy.deepcopy(players) if copy_players else players

    if n_jobs == 1:
        for game_index in range(n):
            winner, _ = run_game(_get_players())
            _game_done(winner)
    else:
        Executor = ThreadPoolExecutor if use_thread_pool else ProcessPoolExecutor
        with Executor(max_workers=n_jobs) as pool:
            futures = [pool.submit(run_game, _get_players()) for _ in range(n)]
            for game_index, future in enumerate(as_completed(futures)):
                winner, _ = future.result()
                _game_done(winner)

    for player in stats:
        print(f'Player {player}: {stats[player]}/{n} ({100.0 * stats[player] / n:.2f}%)')

    if show_stats:
        plot_game_statistics(results, friendly_player)

    return results


def run_game(players: List[Player], visualise: bool = False, fps: int = 5) \
        -> Tuple[int, List[Tuple[int, Move]]]:
    """Run a Battlegrounds game between the given players.

    Return the index of the winning player and a list of moves made in the game,
    represented as tuples containing the index of the acting player and the move itself.

    Args:
        players: The agents.
        visualise: Whether to visualise the state of the game.
        fps: The amount of turns to show per second.

    Preconditions:
        - len(players) > 0 and len(players) % 2 == 0

    Implementation notes:
        - We call pygame.time.wait to animate the visualisation (drawing one turn at a time).
          NOTE: You won't be able to close the pygame window while the animation is in
          progress, only after it's done. But you can still stop the Python interpreter
          altogether by clicking the red square button in PyCharm.
    """
    if visualise:
        # To keep from importing pygame unless needed, only import the visulisation library
        # if we actually need to visualise the games.
        from hsbg.visualisation import init_display, flip_display, close_display, draw_game
        screen = init_display()
    else:
        screen = None

    game = BattlegroundsGame(num_players=len(players))
    move_sequence = []
    while not game.is_done:
        # It is possible for a player to finish the game without doing a matchup.
        # For example, if there are two players left in the game, and one plays
        # a card that deals damage to their hero. In this case, the hero health
        # may be <= 0 and so the game is done.
        #
        # To account for this, only keep simulating if the game hasn't finished yet.
        for index, player in enumerate(players):
            if game.is_done:
                break

            game.start_turn_for_player(index)
            while game.is_turn_in_progress:
                if visualise:
                    draw_game(screen, game, delay=1000 // fps)
                    flip_display()

                move = player.make_move(game)
                game.make_move(move)
                move_sequence.append((index, move))

        if not game.is_done:
            game.next_round()

    if visualise:
        close_display()

    return game.winner, move_sequence


def make_game_statistics(results: List[int], friendly_player: int = 0) -> tuple:
    """Return the game statistics."""
    outcomes = [1 if result == friendly_player else 0 for result in results]
    cumulative_win_probability = [sum(outcomes[0:i]) / i for i in range(1, len(outcomes) + 1)]
    rolling_win_probability = \
        [sum(outcomes[max(i - 50, 0):i]) / min(50, i) for i in range(1, len(outcomes) + 1)]
    return outcomes, cumulative_win_probability, rolling_win_probability


def plot_game_statistics(results: List[int], friendly_player: int = 0) -> None:
    """Plot the outcomes and win probabilities for a given list of Battlegrounds game results.

    Preconditions:
        - all(0 <= r < num_players for r in results)
    """
    outcomes, cumulative_win_probability, rolling_win_probability = make_game_statistics(
        results, friendly_player
    )

    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Scatter(y=outcomes, mode='markers',
                             name='Outcome (1 = Friendly player win, 0 = Enemy player win)'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(y=cumulative_win_probability, mode='lines',
                             name='Friendly player win percentage (cumulative)'),
                  row=2, col=1)
    fig.add_trace(go.Scatter(y=rolling_win_probability, mode='lines',
                             name='Friendly player win percentage (most recent 50 games)'),
                  row=2, col=1)
    fig.update_yaxes(range=[0.0, 1.0], row=2, col=1)

    fig.update_layout(title='Battlegrounds Game Results', xaxis_title='Game')
    fig.show()


def save_game_statistics_to_file(filepath: Union[str, Path], results: List[int],
                                 friendly_player: int = 0) -> None:
    """Save the game statistics to the given file."""
    outcomes, cumulative_win_probability, rolling_win_probability = make_game_statistics(
        results, friendly_player
    )
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w+') as fp:
        json.dump({
            'outcomes': outcomes,
            'cum_win_prob': cumulative_win_probability,
            'rolling_win_prob': rolling_win_probability
        }, fp)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

