"""A module containing visualisation related functionality."""
import math
import pygame
from typing import Tuple, List, Optional

from hsbg.models import Minion
from hsbg import TavernGameBoard, BattlegroundsGame


def visualise_game(surface: pygame.Surface, board: BattlegroundsGame) -> None:
    """Visualise the current state of a battlegrounds game on the given surface.

    This function partitions the given surface into num_players sub-surfaces and draws
    the game state of each player.

    Note that this clears the current contents of the surface.

    Args:
        surface: The surface to draw on.
        board: The board to visualise.
    """
    width, height = surface.get_size()
    sub_surfaces = [... for partition in _partition_rect(width, height, board.num_alive_players)]


def _partition_rect(width: int, height: int, n: int, merit: Optional[callable] = None) \
        -> List[Tuple[int, int, int, int]]:
    """Partition a surface with the given size into n (or more, but as few extra partitions
    as possible) equally sized partitions, so that all the space is used.

    Return a list of tuples containing the left, top, right, and bottom coordinates of each chunk.

    Preconditions:
        - width > 0 and height > 0
        - n > 0

    Implementation details:
        - This function finds the optimal partition size (p, q) by iteratively optimising a given
          merit function, which measures how good a partition size is.
        - Adapted from https://stackoverflow.com/a/5595244/7614083 (License: CC BY-SA 3.0).
    """
    raise NotImplementedError


def visualise_game_board(surface: pygame.Surface, board: TavernGameBoard) -> None:
    """Visualise the current state of a game board on the given surface.
    Note that this clears the current contents of the surface.

    Args:
        surface: The surface to draw on.
        board: The board to visualise.
    """
    # TODO: Draw the hand, the board, and the current minions available for purchase
    # TODO: Draw the current health of the hero.
    raise NotImplementedError


def draw_minion(surface: pygame.Surface, minion: Minion, size: Tuple[int, int], position: Tuple[int, int]) \
        -> None:
    """Draw a minion on the screen at the given position with the given size.

    Args:
        surface: The surface to draw on.
        minion: The minion to draw.
        size: The size of the card representing the minion given as a width-height int tuple.
        position: The centre position of the minion given as an x-y int tuple.
    """
    raise NotImplementedError