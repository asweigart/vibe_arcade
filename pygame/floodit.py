"""
================================================================================
FLOOD-IT GAME
================================================================================
A simple implementation of the classic "Flood-It" puzzle game using Pygame.

HOW TO PLAY:
------------
The board starts as a grid of randomly colored squares. The top-left square
is your "starting territory". Each turn, you pick a color, and every square
in your territory changes to that color. Any neighboring squares that already
have that new color get absorbed into your territory.

The goal is to make the ENTIRE board a single color before you run out of
moves. Click a color button at the bottom (or press number keys 1-6) to
choose your next color.

HOW TO RUN:
-----------
1. Make sure Python 3 is installed.
2. Install pygame:    pip install pygame
3. Run this file:     python floodit.py

HOW TO TWEAK THE GAME:
----------------------
Nearly every number and color you might want to change is a CONSTANT at the
top of this file (written in ALL_CAPS). Read the comments next to each one
for suggestions. Want a harder game? Increase BOARD_SIZE or add more colors.
Want it easier? Lower BOARD_SIZE or raise MAX_MOVES_MULTIPLIER.
================================================================================
"""

# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
# `pygame` is the library that handles drawing graphics, reading input, and
# running the game loop. `random` is used to fill the board with random colors.
# `sys` lets us cleanly exit the program.
import pygame
import random
import sys


# ==============================================================================
# CONSTANTS - change these to customize the game!
# ==============================================================================
# Constants are values that never change while the game runs. By convention,
# Python programmers write them in ALL_CAPS so they're easy to spot.

# ------------------------------------------------------------------------------
# BOARD / GAMEPLAY SETTINGS
# ------------------------------------------------------------------------------

# How many squares wide AND tall the board is (it's always square-shaped).
# Try 8 for a very easy game, 14 for the "classic" experience, or 20+ for
# a real challenge. Values above ~30 may be slow or hard to see.
BOARD_SIZE = 14

# How many different colors appear on the board.
# This MUST match the number of entries in the COLORS list below.
# Fewer colors = easier game. Classic Flood-It uses 6.
NUM_COLORS = 6

# This controls the "move budget". The maximum number of moves allowed is:
#    MAX_MOVES = int(BOARD_SIZE * MAX_MOVES_MULTIPLIER)
# So with BOARD_SIZE=14 and multiplier=1.8 you get 25 moves.
# Raise this to make the game more forgiving; lower it to crank up difficulty.
MAX_MOVES_MULTIPLIER = 1.8

# ------------------------------------------------------------------------------
# VISUAL / WINDOW SETTINGS
# ------------------------------------------------------------------------------

# How many pixels each board square occupies.
# Bigger = larger window and easier to see; smaller = more compact.
CELL_SIZE = 35

# How much empty space (in pixels) to leave around the board inside the window.
# This gives room for the title at the top and color buttons at the bottom.
MARGIN = 20

# Size of the color-picker buttons at the bottom of the screen.
BUTTON_SIZE = 50

# Spacing (in pixels) between adjacent color buttons.
BUTTON_SPACING = 10

# Height reserved at the top of the window for the title and move counter.
HEADER_HEIGHT = 80

# Height reserved at the bottom of the window for the color buttons.
FOOTER_HEIGHT = BUTTON_SIZE + 2 * MARGIN

# How many frames per second the game tries to run at.
# 60 is smooth; you rarely need more for a turn-based game like this.
FPS = 60

# ------------------------------------------------------------------------------
# COLOR PALETTE
# ------------------------------------------------------------------------------
# Each color is an (R, G, B) tuple: three numbers from 0 to 255.
# Feel free to swap these for any colors you like - just keep them visually
# distinct from each other so the game stays readable.
# IMPORTANT: the number of entries here must equal NUM_COLORS above.
COLORS = [
    (220,  50,  50),   # red
    (240, 170,  40),   # orange
    (245, 220,  60),   # yellow
    ( 80, 190,  90),   # green
    ( 70, 130, 220),   # blue
    (170,  90, 200),   # purple
]

# UI colors (used for the background, text, borders, etc.).
# These don't affect gameplay - only how the game looks.
BACKGROUND_COLOR = ( 30,  30,  40)   # dark bluish-gray behind everything
TEXT_COLOR       = (240, 240, 240)   # near-white, used for all text
BORDER_COLOR     = ( 15,  15,  20)   # subtle dark outline around cells/buttons
HIGHLIGHT_COLOR  = (255, 255, 255)   # white outline on the currently-active color
WIN_TEXT_COLOR   = (120, 255, 120)   # green "You Win!" message
LOSE_TEXT_COLOR  = (255, 120, 120)   # red "Game Over" message

# ------------------------------------------------------------------------------
# FONT SETTINGS
# ------------------------------------------------------------------------------
# `None` for the font name tells pygame to use its default font.
# You can also pass a string like "arial" if you want a specific system font.
FONT_NAME = None
FONT_SIZE_LARGE = 36   # used for title and end-of-game messages
FONT_SIZE_SMALL = 22   # used for the move counter and restart hint

# ==============================================================================
# DERIVED VALUES - calculated from the constants above. You usually don't need
# to edit these directly; changing the constants above will update them.
# ==============================================================================

# Total pixel size of just the board (without margins or header/footer).
BOARD_PIXEL_SIZE = BOARD_SIZE * CELL_SIZE

# The full window width and height, in pixels.
WINDOW_WIDTH = BOARD_PIXEL_SIZE + 2 * MARGIN
WINDOW_HEIGHT = HEADER_HEIGHT + BOARD_PIXEL_SIZE + FOOTER_HEIGHT

# The maximum number of moves the player has before losing.
MAX_MOVES = int(BOARD_SIZE * MAX_MOVES_MULTIPLIER)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_board():
    """
    Creates a new random board.

    The board is a 2D list (a list of lists). Each inner list is one ROW.
    Each entry in a row is an integer from 0 to NUM_COLORS-1, representing
    which color that cell is (an index into the COLORS list).

    Example for a 3x3 board:
        [[0, 2, 1],
         [1, 1, 2],
         [0, 2, 0]]
    """
    # We use a "list comprehension" here. This is a compact way to build lists.
    # The outer loop (`for _ in range(BOARD_SIZE)`) runs once per row.
    # The inner loop creates one row's worth of random color indices.
    # The underscore `_` is a Python convention meaning "I don't use this value".
    return [
        [random.randint(0, NUM_COLORS - 1) for _ in range(BOARD_SIZE)]
        for _ in range(BOARD_SIZE)
    ]


def flood_fill(board, new_color):
    """
    Performs the core "flood" action of the game.

    Starting from the top-left cell (0, 0), this function finds every cell
    that is connected to it by matching colors, and changes them all to
    `new_color`. "Connected" means you can reach the cell by stepping up,
    down, left, or right through same-colored neighbors.

    Returns True if any cells actually changed, False if the move did nothing
    (for example, if the player picked the color they're already on).
    """
    # The color currently occupying the top-left "territory".
    original_color = board[0][0]

    # If the player picked the color they're already on, there's nothing to do.
    # Returning False lets the main loop know this move shouldn't count.
    if original_color == new_color:
        return False

    # We use an iterative flood-fill with a stack (list used as a stack).
    # Starting point: the top-left cell. We'll expand outward from here.
    # Each item on the stack is an (row, col) position we still need to process.
    stack = [(0, 0)]

    while stack:
        # `pop()` removes and returns the LAST item added - that's the "stack"
        # behavior (last-in, first-out). This is a classic flood-fill pattern.
        row, col = stack.pop()

        # Skip positions that are off the edge of the board.
        if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
            continue

        # Only flood cells that currently match the ORIGINAL territory color.
        # Cells that are already `new_color` or any other color are boundaries.
        if board[row][col] != original_color:
            continue

        # This cell is part of the territory - change its color.
        board[row][col] = new_color

        # Now add its 4 neighbors (up, down, left, right) to the stack so we
        # can check them next. Diagonals don't count in Flood-It!
        stack.append((row - 1, col))   # up
        stack.append((row + 1, col))   # down
        stack.append((row, col - 1))   # left
        stack.append((row, col + 1))   # right

    # We changed at least the starting cell, so the move counted.
    return True


def is_board_solved(board):
    """
    Returns True if every cell on the board is the same color.

    We do this by grabbing the top-left color, then checking if any cell
    anywhere disagrees with it. As soon as we find a mismatch, we can stop
    and return False (an "early exit" optimization).
    """
    target_color = board[0][0]
    for row in board:
        for cell in row:
            if cell != target_color:
                return False
    return True


def get_button_rect(index):
    """
    Returns the pygame.Rect (rectangle) for a color-picker button.

    `index` is which button (0 for the first color, 1 for the second, etc.).
    We calculate the position so all buttons are centered horizontally in
    the footer area.
    """
    # Total width occupied by all the buttons plus the gaps between them.
    total_width = NUM_COLORS * BUTTON_SIZE + (NUM_COLORS - 1) * BUTTON_SPACING

    # Left edge of the first button, centered in the window.
    start_x = (WINDOW_WIDTH - total_width) // 2

    # X and Y position of this particular button.
    x = start_x + index * (BUTTON_SIZE + BUTTON_SPACING)
    y = HEADER_HEIGHT + BOARD_PIXEL_SIZE + MARGIN

    return pygame.Rect(x, y, BUTTON_SIZE, BUTTON_SIZE)


# ==============================================================================
# DRAWING FUNCTIONS
# ==============================================================================
# These functions handle painting things on the screen. They take the `screen`
# (the pygame surface we draw onto) as their first argument.

def draw_board(screen, board):
    """Draws every cell of the board as a colored square."""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            # Work out where on the screen this cell should appear.
            # MARGIN shifts right, HEADER_HEIGHT shifts down below the title.
            x = MARGIN + col * CELL_SIZE
            y = HEADER_HEIGHT + row * CELL_SIZE

            # Look up the color for this cell from the COLORS palette.
            color = COLORS[board[row][col]]

            # Draw the filled square.
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))

            # Draw a thin outline so adjacent same-colored cells are still
            # visible as separate squares. Set the last argument to 0 (or
            # delete this line) if you prefer a seamless look.
            pygame.draw.rect(screen, BORDER_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)


def draw_buttons(screen, current_color):
    """
    Draws the color-picker buttons at the bottom of the window.

    `current_color` is the color index of the player's current territory;
    we highlight that button so the player can see what color they're on.
    """
    for i in range(NUM_COLORS):
        rect = get_button_rect(i)

        # Fill the button with its color.
        pygame.draw.rect(screen, COLORS[i], rect)

        # Draw a dark border around every button.
        pygame.draw.rect(screen, BORDER_COLOR, rect, 2)

        # If this is the player's current territory color, draw a bright
        # outline on top to mark it. Players can't usefully pick this one.
        if i == current_color:
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect, 4)


def draw_header(screen, font_large, font_small, moves_used, game_state):
    """
    Draws the title, the move counter, and end-of-game messages (if any).

    `game_state` is one of: "playing", "won", "lost".
    """
    # --- Title text ---
    title_surface = font_large.render("FLOOD-IT", True, TEXT_COLOR)
    title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, MARGIN + 10))
    screen.blit(title_surface, title_rect)

    # --- Move counter below the title ---
    # The f"..." syntax is an "f-string" - Python inserts the variable values
    # wherever you put curly braces.
    moves_text = f"Moves: {moves_used} / {MAX_MOVES}"
    moves_surface = font_small.render(moves_text, True, TEXT_COLOR)
    moves_rect = moves_surface.get_rect(center=(WINDOW_WIDTH // 2, MARGIN + 50))
    screen.blit(moves_surface, moves_rect)

    # --- End-of-game banner, shown over the middle of the board ---
    if game_state == "won":
        end_text = "You Win!  Press R to play again"
        end_color = WIN_TEXT_COLOR
    elif game_state == "lost":
        end_text = "Game Over!  Press R to try again"
        end_color = LOSE_TEXT_COLOR
    else:
        end_text = None

    if end_text is not None:
        # A semi-transparent dark rectangle so the text is readable against
        # the board. We build it as a separate Surface and set its alpha
        # (transparency) to 180 out of 255.
        overlay = pygame.Surface((WINDOW_WIDTH, 60))
        overlay.set_alpha(180)
        overlay.fill(BACKGROUND_COLOR)
        overlay_y = HEADER_HEIGHT + BOARD_PIXEL_SIZE // 2 - 30
        screen.blit(overlay, (0, overlay_y))

        end_surface = font_large.render(end_text, True, end_color)
        end_rect = end_surface.get_rect(
            center=(WINDOW_WIDTH // 2, overlay_y + 30)
        )
        screen.blit(end_surface, end_rect)


# ==============================================================================
# MAIN GAME FUNCTION
# ==============================================================================

def main():
    """Sets up pygame and runs the main game loop."""
    # Initialize all pygame modules (sound, video, input, etc.).
    pygame.init()

    # Create the actual window. The tuple (WIDTH, HEIGHT) is its size.
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # This text appears in the window's title bar.
    pygame.display.set_caption("Flood-It")

    # `Clock` lets us cap the frame rate so the game doesn't waste CPU.
    clock = pygame.time.Clock()

    # Create the two font objects we'll use for drawing text.
    font_large = pygame.font.Font(FONT_NAME, FONT_SIZE_LARGE)
    font_small = pygame.font.Font(FONT_NAME, FONT_SIZE_SMALL)

    # ----- Set up the initial game state -----
    board = create_board()
    moves_used = 0
    game_state = "playing"   # will become "won" or "lost" later

    # ----- The main game loop -----
    # This loop runs once per frame. It: handles events (input), updates the
    # game state, and redraws the screen. It keeps running until the player
    # closes the window.
    running = True
    while running:

        # ---------- 1. HANDLE EVENTS (input) ----------
        # Pygame queues up every keypress, mouse click, window close, etc.
        # We loop through them all and respond to the ones we care about.
        for event in pygame.event.get():

            # The player clicked the window's close button.
            if event.type == pygame.QUIT:
                running = False

            # A key was pressed down.
            elif event.type == pygame.KEYDOWN:

                # "R" restarts the game at any time (during or after play).
                if event.key == pygame.K_r:
                    board = create_board()
                    moves_used = 0
                    game_state = "playing"

                # Number keys 1..NUM_COLORS pick a color (keyboard shortcut).
                # pygame.K_1 is the "1" key, K_2 is "2", etc., and they
                # happen to be consecutive numbers we can do math on.
                elif game_state == "playing":
                    for i in range(NUM_COLORS):
                        if event.key == pygame.K_1 + i:
                            # Attempt the flood. If nothing changed (picked
                            # the same color), don't count it as a move.
                            if flood_fill(board, i):
                                moves_used += 1

            # The player pressed a mouse button.
            elif event.type == pygame.MOUSEBUTTONDOWN and game_state == "playing":
                # `event.pos` is an (x, y) tuple of where they clicked.
                # Only the LEFT mouse button (event.button == 1) triggers a move.
                if event.button == 1:
                    for i in range(NUM_COLORS):
                        # `collidepoint` checks if a point is inside a Rect.
                        if get_button_rect(i).collidepoint(event.pos):
                            if flood_fill(board, i):
                                moves_used += 1
                            # Stop checking once we've found the clicked button.
                            break

        # ---------- 2. UPDATE GAME STATE ----------
        # After any move, check whether the player has won or lost.
        # We only do this while they're still "playing" - once the game ends
        # we freeze the state until they press R to restart.
        if game_state == "playing":
            if is_board_solved(board):
                game_state = "won"
            elif moves_used >= MAX_MOVES:
                game_state = "lost"

        # ---------- 3. DRAW EVERYTHING ----------
        # Always start by wiping the screen with the background color, so old
        # frames don't leave ghost images behind.
        screen.fill(BACKGROUND_COLOR)

        # Draw the pieces of the UI, back-to-front (things drawn later appear
        # on top of things drawn earlier).
        draw_board(screen, board)
        draw_buttons(screen, board[0][0])
        draw_header(screen, font_large, font_small, moves_used, game_state)

        # `flip` shows everything we just drew. Without this line, the window
        # would never visibly update!
        pygame.display.flip()

        # Wait just long enough to keep the frame rate at FPS.
        clock.tick(FPS)

    # ----- Clean up -----
    # When the loop exits, shut pygame down and end the program cleanly.
    pygame.quit()
    sys.exit()


# ==============================================================================
# ENTRY POINT
# ==============================================================================
# This special `if` block means "only run main() if this file was executed
# directly" (as opposed to being imported as a module from another script).
# It's a common Python pattern that makes your code more reusable.
if __name__ == "__main__":
    main()
