"""A module containing visualisation related functionality."""
import math
import pygame
from typing import Tuple, List, Optional

from hsbg.models import Minion
from hsbg import TavernGameBoard, BattlegroundsGame
from hsbg.combat import SIMULATOR_ABILITIES


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
    def _default_merit_function(partition_width: float, partition_height: float) -> float:
        """Default merit function that looks at how close the aspect ratios are.
        The closer, the higher the merit.
        """
        target_ratio = width / height
        current_ratio = partition_width / partition_height
        return 1 / math.exp((target_ratio - current_ratio)**2)

    merit_function = merit or _default_merit_function

    best_merit_yet = float('-inf')
    best_configuration_yet = None
    for p in range(math.floor(math.sqrt(n)), 0, -1):
        q = math.ceil(n / p)
        merit1 = merit_function(width / p, height / q)
        merit2 = merit_function(width / q, height / p)
        current_merit = max(merit1, merit2)
        if current_merit > best_merit_yet:
            # Update best_merit_yet
            best_merit_yet = current_merit
            # Update best_configuration_yet
            if merit1 > merit2:
                best_configuration_yet = (p, q)
            else:
                best_configuration_yet = (q, p)

    # TODO: Partition based on best_configuration_yet
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


def initialize_screen(screen_size: tuple[int, int], allowed: list) -> pygame.Surface:
    """Initialize pygame and the display window.

    allowed is a list of pygame event types that should be listened for while pygame is running.
    """
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screen_size)
    screen.fill((255, 255, 255))
    pygame.display.flip()

    pygame.event.clear()
    pygame.event.set_blocked(None)
    pygame.event.set_allowed([pygame.QUIT] + allowed)

    return screen


def draw_text(screen: pygame.Surface, text: str, pos: tuple[int, int]) -> None:
    """Draw the given text to the pygame screen at the given position.

    pos represents the *upper-left corner* of the text.
    """
    font_size = min(20 * screen.get_height() // 1080, 20 * screen.get_width() // 1980)
    font = pygame.font.SysFont('inconsolata', font_size)
    text_surface = font.render(text, True, (0, 0, 0))
    width, height = text_surface.get_size()
    screen.blit(text_surface,
                pygame.Rect(pos, (pos[0] + width, pos[1] + height)))


def draw_minion(surface: pygame.Surface, minion: Minion, size: Tuple[int, int],
                position: Tuple[int, int]) -> None:
    """Draw a minion on the screen at the given position with the given size.

    Args:
        surface: The surface to draw on.
        minion: The minion to draw.
        size: The size of the card representing the minion given as a width-height int tuple.
        position: The centre position of the minion given as an x-y int tuple.
    """
    card_w, card_l = size
    x, y = position
    font_padding = 22 // 4
    # padding within the card
    side = card_w // (25 // 3)
    color = (218, 165, 32) if minion.is_golden else (0, 0, 0)

    # CARD ITSELF
    pygame.draw.rect(surface, color, (x, y, card_w, card_l), 2)

    # TIER LEVEL
    pygame.draw.rect(surface, color, (x, y, card_w // 5, card_l // 6), 2)
    draw_text(surface, str(minion.tier),
              (x + card_w // 10 - font_padding, y + card_l // 12 - font_padding))

    # MONSTER TYPE
    pygame.draw.rect(surface, color,
                     (x + side, y + 2 * card_l // 3 - side, card_w - side * 2, side), 2)
    draw_text(surface, str(minion.card_class.name),
              (x + side + (card_w - side * 2) // 4, y + 2 * card_l // 3 - side + side // 4))

    # ATTACK
    pygame.draw.rect(surface, color, (x, y + card_l - card_l // 6, card_w // 5, card_l // 6), 2)
    draw_text(surface, str(minion.attack),
              (x + card_w // 10 - font_padding, y + card_l - card_l // 12 - font_padding))

    # HEALTH
    pygame.draw.rect(surface, color, (x + card_w - card_w // 5, y + card_l - card_l // 6,
                                      card_w // 5, card_l // 6), 2)
    draw_text(surface, str(minion.health),
              (x + card_w - card_w // 10 - font_padding, y + card_l - card_l // 12 - font_padding))

    # NAME
    # TODO: Fix the name and all the text including colour and shit
    pygame.draw.rect(surface, color, (x + side // 2, y + card_l // 2 - card_l // 6,
                                      card_w - side, card_l // 6), 2)
    draw_text(surface, str(minion.name), (x + side // 2 + 4,
                                          y + card_l // 2 - card_l // 6 + 10))

    # ABILITIES (ONLY THE ONES THE SIMULATOR CAN HANDLE)
    pygame.draw.rect(surface, color, (x + card_w - card_w // 2, y, card_w // 2, card_l // 6), 2)
    abilities_to_draw = [x.name[0] for x in SIMULATOR_ABILITIES if x in minion.current_abilities]
    draw_text(surface, str(','.join(abilities_to_draw)),
              (x + card_w - card_w // 2 + 5, y + card_l // 12 - font_padding))


if __name__ == '__main__':
    from hsbg import minions
    # from hsbg.models import Buff
    # Draw the following game state:
    # Board
    #   * Pack Leader
    #   * Alleycat
    # Hand
    #   * Kindly Grandmother
    #   * Scavenging Hyena
    board = TavernGameBoard()
    board.next_turn()
    board.add_minion_to_hand(minions.ALLEYCAT)
    board.add_minion_to_hand(minions.KINDLY_GRANDMOTHER)
    board.add_minion_to_hand(minions.SCAVENGING_HYENA)
    board.play_minion(0)
    board.play_minion(1)

    BACKGROUND_COLOUR = (255, 255, 255)
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080

    pygame.init()
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

    running = True
    while running:
        # Search for a quit event
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # Fill the background
        screen.fill(BACKGROUND_COLOUR)

        # visualise_game_board(screen, board)
        card_width = SCREEN_WIDTH // 10
        card_length = card_width * 6 // 5
        draw_minion(screen, board.board[0], (card_width, card_length), (800, 800))

        # Flip screen buffers
        pygame.display.flip()

    pygame.quit()
