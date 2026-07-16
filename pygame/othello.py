"""
================================================================================
  OTHELLO / REVERSI
  A simple two-player Othello game built with Pygame.
================================================================================

HOW TO PLAY
-----------
  * Black moves first.
  * On your turn, click an empty square to place one of your discs.
  * A move is only legal if it "sandwiches" one or more of your opponent's
    discs in a straight line (horizontal, vertical, or diagonal) between the
    disc you just placed and another of your own discs.
  * Every sandwiched disc flips to your color.
  * If you have no legal moves, your turn is skipped automatically.
  * The game ends when neither player can move (usually when the board is
    full). Whoever has the most discs wins.

HOW TO RUN
----------
  1. Install Python 3.8+ and Pygame:    pip install pygame
  2. Save this file as `othello.py`
  3. From a terminal:                   python othello.py

CONTROLS
--------
  * Mouse click ........... place a disc on the highlighted square
  * R ..................... restart the game
  * H ..................... toggle the "legal move" hint dots
  * ESC or window close ... quit

STRUCTURE OF THIS FILE
----------------------
  1. Imports
  2. CONSTANTS (colors, sizes, gameplay toggles) -- tweak these!
  3. Derived constants (computed from the ones above -- don't edit by hand)
  4. Board logic (pure Python, no drawing)
  5. Drawing functions (all Pygame rendering)
  6. The main() function (the game loop that ties it all together)

The code is intentionally verbose and commented for readers who are new to
Python or Pygame. Feel free to delete comments once they stop being useful.
================================================================================
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
# `sys`    - used only to cleanly exit the program with sys.exit()
# `pygame` - the game library that does all the window/drawing/input work
import sys
import pygame


# ==============================================================================
# 2. CONSTANTS  --  tweak these to change how the game looks and behaves
# ==============================================================================
# Constants are just variables we promise never to change while the game runs.
# By convention in Python, constants are written in UPPER_CASE_WITH_UNDERSCORES.
# Gathering them at the top makes the game easy to customize without hunting
# through the code.

# ---- Board size ----------------------------------------------------------------
# The classic Othello board is 8x8. The code is written so that any even number
# from 4 upward should work -- try 6 for a quick game or 10 for a longer one.
# Odd numbers technically work but the starting position looks off-center.
BOARD_SIZE = 8

# ---- Pixel sizes ---------------------------------------------------------------
# SQUARE_SIZE is the width & height of one board cell in pixels.
# Bigger = easier to click, but needs a bigger window. 60 is a good default;
# try 80 on a large monitor or 48 on a laptop.
SQUARE_SIZE = 72

# Width of the thin grid lines drawn between squares. 1-3 pixels looks best.
GRID_LINE_WIDTH = 2

# Pixels of padding between the disc and the edge of its square. Smaller
# values = bigger discs. Try 6 for a chunky look or 14 for a delicate one.
DISC_PADDING = 8

# Height of the status bar at the bottom of the window (shows score & turn).
STATUS_BAR_HEIGHT = 80

# Frames per second. 30 is plenty for a board game. Higher = smoother
# animations but more CPU use.
FPS = 30

# ---- Colors --------------------------------------------------------------------
# Colors in Pygame are (Red, Green, Blue) tuples, each from 0 to 255.
# Think of it as mixing three colored lights: (0,0,0) is black, (255,255,255)
# is white, (255,0,0) is pure red, etc. Swap these to reskin the game.

# Background behind the board -- a deep wood-ish brown.
BACKGROUND_COLOR = (40, 30, 20)

# The classic green felt of an Othello board.
BOARD_COLOR = (30, 120, 60)

# Grid lines between squares. A darker green than the board for subtle contrast.
GRID_COLOR = (15, 70, 35)

# Disc colors. The real game uses pure black & white; I softened them slightly
# so the discs don't feel harsh on the eyes.
BLACK_DISC_COLOR = (25, 25, 25)
WHITE_DISC_COLOR = (240, 240, 235)

# Outline drawn around each disc so white discs stand out on the green board.
DISC_OUTLINE_COLOR = (10, 10, 10)
DISC_OUTLINE_WIDTH = 2

# Color of the small dot shown on squares where the current player may move.
# The alpha value (4th number, 0-255) makes it semi-transparent.
HINT_COLOR = (255, 255, 255, 90)

# Highlight drawn on the square currently under the mouse cursor (if legal).
HOVER_COLOR = (255, 255, 180, 70)

# Text color used for the status bar at the bottom.
TEXT_COLOR = (235, 235, 225)

# ---- Gameplay toggles ----------------------------------------------------------
# Show small dots on squares the current player is allowed to play?
# Set to False for a more challenging "figure it out yourself" experience.
SHOW_HINTS_BY_DEFAULT = True

# Should the starting four discs be placed in the standard Othello pattern?
# True = official rules (diagonal: white top-left / black top-right).
# Leave this True unless you're experimenting with variants.
USE_STANDARD_OPENING = True

# ---- Fonts ---------------------------------------------------------------------
# Pygame can load system fonts by name. `None` falls back to Pygame's default.
# Try "arial", "couriernew", or "georgia" -- availability depends on your OS.
FONT_NAME = None
FONT_SIZE = 28


# ==============================================================================
# 3. DERIVED CONSTANTS  --  computed automatically; don't edit by hand
# ==============================================================================
# These are determined by the constants above. Keeping them separate means
# if you change SQUARE_SIZE, the window resizes itself correctly.

# Total width of the board area (all squares side by side).
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE

# Full window size: the board plus the status bar below it.
WINDOW_WIDTH = BOARD_PIXELS
WINDOW_HEIGHT = BOARD_PIXELS + STATUS_BAR_HEIGHT

# Numbers used to represent the contents of each square internally.
# Using constants instead of raw numbers makes the code much more readable --
# `board[r][c] == BLACK` is much clearer than `board[r][c] == 1`.
EMPTY = 0
BLACK = 1
WHITE = 2

# The eight directions a "sandwich" of discs can run: combinations of
# -1 (up/left), 0 (no change), and +1 (down/right), excluding (0, 0).
# Each tuple is (row_delta, column_delta).
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]


# ==============================================================================
# 4. BOARD LOGIC  --  pure game rules; no drawing code here
# ==============================================================================
# Keeping the rules separate from the drawing makes each part easier to read,
# test, and modify. Every function below works with a plain Python list of
# lists (`board[row][col]`) and doesn't touch the screen at all.


def create_initial_board():
    """Build a fresh board with the four starting discs in the middle.

    The board is a 2D list: `board[row][col]` where row 0 is the top row.
    Every cell starts as EMPTY, then we drop the four opening discs in the
    center four squares according to standard Othello rules.
    """
    # A list comprehension that makes a BOARD_SIZE x BOARD_SIZE grid of EMPTYs.
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    if USE_STANDARD_OPENING:
        # The four starting squares sit at the exact center of the board.
        # For an 8x8 board these are (3,3), (3,4), (4,3), (4,4).
        mid = BOARD_SIZE // 2
        board[mid - 1][mid - 1] = WHITE
        board[mid - 1][mid    ] = BLACK
        board[mid    ][mid - 1] = BLACK
        board[mid    ][mid    ] = WHITE

    return board


def opponent_of(player):
    """Return the color that ISN'T `player`. Useful all over the rules code."""
    return WHITE if player == BLACK else BLACK


def in_bounds(row, col):
    """Return True if (row, col) sits inside the board grid."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def discs_flipped_by_move(board, row, col, player):
    """Return the list of (row, col) positions that would flip if `player`
    played at (row, col). Returns an empty list if the move is illegal.

    The rule: starting from the placed disc, walk outward in each of the
    eight directions. To flip anything in a direction we must pass over
    one or more opponent discs and then land on one of our own. If we hit
    the edge of the board or an empty square first, nothing flips that way.
    """
    # You can't play on an occupied square, so bail out early.
    if board[row][col] != EMPTY:
        return []

    other = opponent_of(player)
    all_flips = []  # Every opponent disc we'll capture across all directions.

    for d_row, d_col in DIRECTIONS:
        # Step one cell in this direction to begin scanning.
        r, c = row + d_row, col + d_col
        potential_flips = []

        # Walk forward as long as we see opponent discs.
        while in_bounds(r, c) and board[r][c] == other:
            potential_flips.append((r, c))
            r += d_row
            c += d_col

        # After the walk, we only capture those discs if we ended on our
        # OWN color -- that closes the sandwich. Hitting an empty square or
        # going off the edge means this direction contributes nothing.
        if potential_flips and in_bounds(r, c) and board[r][c] == player:
            all_flips.extend(potential_flips)

    return all_flips


def is_legal_move(board, row, col, player):
    """A move is legal if it flips at least one opponent disc."""
    return len(discs_flipped_by_move(board, row, col, player)) > 0


def find_all_legal_moves(board, player):
    """Return a list of every (row, col) where `player` may legally play."""
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if is_legal_move(board, r, c, player):
                moves.append((r, c))
    return moves


def apply_move(board, row, col, player):
    """Place a disc and flip everything the move captures. Assumes legal."""
    flips = discs_flipped_by_move(board, row, col, player)
    board[row][col] = player
    for r, c in flips:
        board[r][c] = player


def count_discs(board):
    """Return (black_count, white_count) across the whole board."""
    black = sum(row.count(BLACK) for row in board)
    white = sum(row.count(WHITE) for row in board)
    return black, white


# ==============================================================================
# 5. DRAWING FUNCTIONS  --  all the Pygame rendering lives down here
# ==============================================================================
# Each function takes the Pygame `screen` (the thing we draw onto) plus any
# data it needs, and paints a part of the frame. `main()` calls them in order
# once per frame.


def draw_board_background(screen):
    """Paint the green playing surface and the grid lines on top of it."""
    # `pygame.Rect(left, top, width, height)` describes a rectangle in pixels.
    board_rect = pygame.Rect(0, 0, BOARD_PIXELS, BOARD_PIXELS)
    pygame.draw.rect(screen, BOARD_COLOR, board_rect)

    # Vertical grid lines -- one at every column boundary.
    for col in range(BOARD_SIZE + 1):
        x = col * SQUARE_SIZE
        pygame.draw.line(screen, GRID_COLOR,
                         (x, 0), (x, BOARD_PIXELS), GRID_LINE_WIDTH)

    # Horizontal grid lines.
    for row in range(BOARD_SIZE + 1):
        y = row * SQUARE_SIZE
        pygame.draw.line(screen, GRID_COLOR,
                         (0, y), (BOARD_PIXELS, y), GRID_LINE_WIDTH)


def draw_discs(screen, board):
    """Draw every placed disc as a filled circle with a thin outline."""
    radius = SQUARE_SIZE // 2 - DISC_PADDING

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                continue  # Nothing to draw on empty squares.

            # Center of this cell in pixel coordinates.
            center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2

            color = BLACK_DISC_COLOR if board[r][c] == BLACK else WHITE_DISC_COLOR
            pygame.draw.circle(screen, color, (center_x, center_y), radius)
            pygame.draw.circle(screen, DISC_OUTLINE_COLOR,
                               (center_x, center_y), radius, DISC_OUTLINE_WIDTH)


def draw_hints(screen, legal_moves):
    """Draw a small translucent dot on each legal-move square.

    Transparency in Pygame requires drawing onto a temporary `Surface` with
    the SRCALPHA flag, then blitting that surface onto the real screen.
    """
    hint_radius = SQUARE_SIZE // 8  # Roughly one-eighth of a square -- subtle.

    for r, c in legal_moves:
        # Create a transparent square the size of one cell.
        hint_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(
            hint_surface, HINT_COLOR,
            (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
            hint_radius,
        )
        screen.blit(hint_surface, (c * SQUARE_SIZE, r * SQUARE_SIZE))


def draw_hover_highlight(screen, mouse_pos, legal_moves):
    """Tint the square under the cursor if the current player can play there."""
    mx, my = mouse_pos

    # Bail out if the mouse is below the board (inside the status bar).
    if my >= BOARD_PIXELS:
        return

    # Convert pixel coordinates to grid coordinates.
    col = mx // SQUARE_SIZE
    row = my // SQUARE_SIZE

    if (row, col) not in legal_moves:
        return

    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    highlight.fill(HOVER_COLOR)
    screen.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def draw_status_bar(screen, font, board, current_player, game_over, winner_text):
    """Draw the black strip below the board showing score, turn, or winner."""
    # Black background behind all text.
    bar_rect = pygame.Rect(0, BOARD_PIXELS, WINDOW_WIDTH, STATUS_BAR_HEIGHT)
    pygame.draw.rect(screen, BACKGROUND_COLOR, bar_rect)

    black_count, white_count = count_discs(board)

    if game_over:
        main_text = winner_text
    else:
        turn_name = "Black" if current_player == BLACK else "White"
        main_text = f"{turn_name}'s turn"

    score_text = f"Black {black_count}   -   White {white_count}"

    # `font.render(text, antialias, color)` produces a ready-to-blit Surface.
    main_surface = font.render(main_text, True, TEXT_COLOR)
    score_surface = font.render(score_text, True, TEXT_COLOR)

    # Center each line horizontally within the status bar.
    main_rect = main_surface.get_rect(
        center=(WINDOW_WIDTH // 2, BOARD_PIXELS + STATUS_BAR_HEIGHT // 3)
    )
    score_rect = score_surface.get_rect(
        center=(WINDOW_WIDTH // 2, BOARD_PIXELS + 2 * STATUS_BAR_HEIGHT // 3)
    )
    screen.blit(main_surface, main_rect)
    screen.blit(score_surface, score_rect)


# ==============================================================================
# 6. MAIN GAME LOOP
# ==============================================================================
# `main()` runs once when the program starts and stays running until the
# player closes the window. Inside it is a big `while` loop called the
# "game loop", which on every iteration:
#   1. Handles input events (clicks, key presses, window close)
#   2. Updates game state (applies moves, switches turns, checks for end)
#   3. Draws the current state of the game
#   4. Waits just long enough to hit the target FPS


def main():
    # Pygame needs to be initialized before any other Pygame calls.
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Othello")

    # `Clock` lets us cap the frame rate so the CPU isn't pegged at 100%.
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)

    # ---- Game state ------------------------------------------------------------
    # Any variable that CAN change during play lives here, not in CONSTANTS.
    board = create_initial_board()
    current_player = BLACK           # Black always moves first in Othello.
    show_hints = SHOW_HINTS_BY_DEFAULT
    game_over = False
    winner_text = ""

    # Pre-compute legal moves for the opening position so the first frame is
    # correct. We'll refresh this whenever the board or turn changes.
    legal_moves = find_all_legal_moves(board, current_player)

    # ---- The game loop ---------------------------------------------------------
    running = True
    while running:

        # ---- 1. Handle events --------------------------------------------------
        # `pygame.event.get()` returns every input that happened since last call.
        for event in pygame.event.get():

            # Player clicked the window's close button.
            if event.type == pygame.QUIT:
                running = False

            # Keyboard presses.
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Restart: rebuild the board from scratch.
                    board = create_initial_board()
                    current_player = BLACK
                    game_over = False
                    winner_text = ""
                    legal_moves = find_all_legal_moves(board, current_player)
                elif event.key == pygame.K_h:
                    show_hints = not show_hints

            # Mouse click -- try to play a disc if the click landed on the board.
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                # event.button 1 = left click. Ignore right/middle clicks.
                if event.button != 1:
                    continue

                mx, my = event.pos
                if my >= BOARD_PIXELS:
                    continue  # Click in the status bar, ignore.

                col = mx // SQUARE_SIZE
                row = my // SQUARE_SIZE

                if (row, col) in legal_moves:
                    apply_move(board, row, col, current_player)

                    # Turn passes to the other player -- UNLESS they have no
                    # legal moves, in which case they pass and it's our turn
                    # again. If NEITHER player has a move, the game ends.
                    next_player = opponent_of(current_player)
                    next_moves = find_all_legal_moves(board, next_player)

                    if next_moves:
                        current_player = next_player
                        legal_moves = next_moves
                    else:
                        # Other player has to pass; check if we can still move.
                        own_moves = find_all_legal_moves(board, current_player)
                        if own_moves:
                            # We keep going; opponent is skipped silently.
                            legal_moves = own_moves
                        else:
                            # Neither side can move -> game over.
                            black, white = count_discs(board)
                            if black > white:
                                winner_text = f"Black wins!  {black} to {white}"
                            elif white > black:
                                winner_text = f"White wins!  {white} to {black}"
                            else:
                                winner_text = f"Tie game!  {black} to {white}"
                            game_over = True
                            legal_moves = []

        # ---- 2. Draw the current frame ----------------------------------------
        # `fill` with the background color first wipes the previous frame.
        screen.fill(BACKGROUND_COLOR)
        draw_board_background(screen)

        if show_hints and not game_over:
            draw_hints(screen, legal_moves)
            draw_hover_highlight(screen, pygame.mouse.get_pos(), legal_moves)

        draw_discs(screen, board)
        draw_status_bar(screen, font, board, current_player, game_over, winner_text)

        # `flip()` swaps the off-screen drawing buffer onto the visible window.
        pygame.display.flip()

        # ---- 3. Cap the frame rate --------------------------------------------
        clock.tick(FPS)

    # Player asked to quit: shut Pygame down cleanly and exit the process.
    pygame.quit()
    sys.exit()


# This is Python's standard "run main() when executed directly, but don't run
# it if this file is imported as a module" idiom. Worth memorizing!
if __name__ == "__main__":
    main()
