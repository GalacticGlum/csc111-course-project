"""A module containing visualisation related functionality.

This file is Copyright (c) 2021 Shon Verch and Grace Lin.
"""
import math
from typing import Tuple, List, Optional
import pygame

from hsbg.models import Minion, MECHANIC_ABILITIES
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
    s_width, s_height = surface.get_size()

    # GOLD
    padding = 5
    pygame.draw.circle(surface, (218, 165, 32),
                       (padding + s_width // 30, padding + s_width // 30), s_width // 30, 2)
    font_padding = min(30 * screen.get_height() // 1080, 30 * screen.get_width() // 1980) // 2
    draw_text_for_board(surface, str(board.gold),
                        (padding + s_width // 30 - font_padding,
                         padding + s_width // 30 - font_padding), (218, 165, 32))

    # TIER
    padding = 5
    pygame.draw.circle(surface, (0, 0, 0),
                       (s_width // 2, padding + s_width // 30), s_width // 30, 2)
    font_padding = min(30 * screen.get_height() // 1080, 30 * screen.get_width() // 1980) // 2
    draw_text_for_board(surface, str(board.tavern_tier),
                        (padding + s_width // 2 - font_padding,
                         padding + s_width // 30 - font_padding))

    # HERO HEALTH
    padding = 5
    pygame.draw.circle(surface, (255, 0, 0),
                       (s_width - padding - s_width // 30,
                        padding + s_width // 30), s_width // 30, 2)
    font_padding = min(30 * screen.get_height() // 1080, 30 * screen.get_width() // 1980) // 2
    draw_text_for_board(surface, str(board.hero_health),
                        (s_width - s_width // 30 - font_padding - padding,
                         padding + s_width // 30 - font_padding), (255, 0, 0))

    # BOB'S SQUADRON
    card_width = SCREEN_WIDTH // 11
    card_length = card_width * 6 // 5
    card_padding = (SCREEN_WIDTH // 10 - card_width) // 2
    for i in range(len(board.recruits)):
        if board.recruits[i] is None:
            continue
        x_pos = card_padding * (i + 1) + card_width * i
        y_pos = 2 * s_height // 9
        draw_minion(surface, board.recruits[i], (card_width, card_length), (x_pos, y_pos))

    # YOUR PLAYED CARDS
    for i in range(len(board.board)):
        if board.board[i] is None:
            continue
        x_pos = card_padding * (i + 1) + card_width * i
        y_pos = 4 * s_height // 9
        draw_minion(surface, board.board[i], (card_width, card_length), (x_pos, y_pos))

    # YOUR HAND
    for i in range(len(board.hand)):
        if board.hand[i] is None:
            continue
        x_pos = card_padding * (i + 1) + card_width * i
        y_pos = 5 * s_height // 7
        draw_minion(surface, board.hand[i], (card_width, card_length), (x_pos, y_pos))


def draw_text_for_board(surface: pygame.Surface, text: str, pos: tuple[int, int],
                        color: tuple = (0, 0, 0)) -> None:
    """Draw the given text to the pygame screen at the given position.

    pos represents the *upper-left corner* of the text.
    """
    font_size = min(50 * surface.get_height() // 1080, 50 * surface.get_width() // 1980)
    font = pygame.font.SysFont('inconsolata', font_size)
    text_surface = font.render(text, True, color)
    width, height = text_surface.get_size()
    surface.blit(text_surface,
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
    font_padding = min(16 * screen.get_height() // 1080, 16 * screen.get_width() // 1980) // 4
    # padding within the card
    side = card_w // (25 // 3)
    color = (218, 165, 32) if minion.is_golden else (0, 0, 0)

    # CARD ITSELF
    pygame.draw.rect(surface, color, (x, y, card_w, card_l), 2)

    # TIER LEVEL
    pygame.draw.rect(surface, color, (x, y, card_w // 5, card_l // 6), 2)
    draw_text_for_card(surface, str(minion.tier),
                       (x + card_w // 10 - font_padding, y + card_l // 12 - font_padding))

    # MONSTER TYPE
    pygame.draw.rect(surface, color,
                     (x + side, y + 2 * card_l // 3 - side, card_w - side * 2, side), 2)
    draw_text_for_card(surface, str(minion.card_class.name),
                       (x + side + (card_w - side * 2) // 4,
                        y + 2 * card_l // 3 - side + side // 4))

    # ATTACK
    pygame.draw.rect(surface, color, (x, y + card_l - card_l // 6, card_w // 5, card_l // 6), 2)
    draw_text_for_card(surface, str(minion.attack),
                       (x + card_w // 10 - font_padding, y + card_l - card_l // 12 - font_padding))

    # HEALTH
    pygame.draw.rect(surface, color, (x + card_w - card_w // 5, y + card_l - card_l // 6,
                                      card_w // 5, card_l // 6), 2)
    draw_text_for_card(surface, str(minion.health),
                       (x + card_w - card_w // 10 - font_padding,
                        y + card_l - card_l // 12 - font_padding))

    # NAME
    # TODO: Fix the name and all the text including colour and shit
    pygame.draw.rect(surface, color, (x + side // 2, y + card_l // 2 - card_l // 6,
                                      card_w - side, card_l // 6), 2)
    draw_text_for_card(surface, str(minion.name), (x + side // 2 + 4,
                                                   y + card_l // 2 - card_l // 6 + 10))

    # ABILITIES (ONLY THE ONES THE SIMULATOR CAN HANDLE)
    pygame.draw.rect(surface, color, (x + card_w - card_w // 2, y, card_w // 2, card_l // 6), 2)
    abilities_to_draw = [a.name[0] for a in MECHANIC_ABILITIES if a in minion.current_abilities]
    draw_text_for_card(surface, str(','.join(abilities_to_draw)),
                       (x + card_w - card_w // 2 + 5, y + card_l // 12 - font_padding))


def draw_text_for_card(surface: pygame.Surface, text: str, pos: tuple[int, int]) -> None:
    """Draw the given text to the pygame screen at the given position.

    pos represents the *upper-left corner* of the text.
    """
    font_size = min(17 * surface.get_height() // 1080, 17 * surface.get_width() // 1980)
    font = pygame.font.SysFont('inconsolata', font_size)
    text_surface = font.render(text, True, (0, 0, 0))
    width, height = text_surface.get_size()
    surface.blit(text_surface,
                 pygame.Rect(pos, (pos[0] + width, pos[1] + height)))


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
    play_board = TavernGameBoard()
    play_board.next_turn()
    play_board.add_minion_to_hand(minions.ALLEYCAT)
    play_board.add_minion_to_hand(minions.KINDLY_GRANDMOTHER)
    play_board.add_minion_to_hand(minions.SCAVENGING_HYENA)
    play_board.add_minion_to_hand(minions.NAT_PAGLE)

    play_board.play_minion(0)
    play_board.play_minion(1)

    BACKGROUND_COLOUR = (255, 255, 255)
    SCREEN_WIDTH, SCREEN_HEIGHT = 1080, 720

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

        visualise_game_board(screen, play_board)
        # w_card = SCREEN_WIDTH // 10
        # l_card = w_card * 6 // 5
        # draw_minion(screen, board.board[0], (w_card_width, l_card), (800, 800))

        # Flip screen buffers
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['math', 'pygame', 'hsbg', 'hsbg.models'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E0602', 'E1136', 'R0913', 'R0914', 'W0703', 'E9969']
    })

    import python_ta.contracts
    python_ta.contracts.check_all_contracts()
