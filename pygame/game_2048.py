"""
========================================================================
2048 - A Sliding Tile Puzzle Game
========================================================================

A simple implementation of the popular 2048 game, written in Python
using the Pygame library. This file is heavily commented and intended
as a TEACHING EXAMPLE for people new to programming.

HOW TO PLAY:
    - Use the ARROW KEYS to slide all tiles in one direction.
    - When two tiles with the SAME number touch, they merge into one
      tile whose value is the sum of the two.
    - Each turn, a new tile (a 2 or a 4) appears in a random empty cell.
    - You WIN when you create a tile with the value 2048.
    - You LOSE when the board is full and no moves are possible.
    - Press R to restart the game at any time.

HOW TO RUN:
    1. Install Python 3.
    2. Install Pygame:        pip install pygame
    3. Run the game:          python game_2048.py

LEARNING GOALS COVERED IN THIS FILE:
    - Variables, constants, and naming conventions
    - Lists and 2D lists (the game grid)
    - Functions and how to break a program into small pieces
    - Game loops and event handling
    - Basic graphics: drawing rectangles and text
    - A little bit of game logic (sliding/merging tiles)

Feel free to tweak the CONSTANTS section below — that's where most of
the fun experiments live!
========================================================================
"""

# ------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------
# `pygame` is the library that handles drawing graphics, the window,
# keyboard input, and timing. Think of it as a toolbox for making games.
#
# `random` is part of Python's standard library. We use it to pick
# random spots on the board for new tiles, and to choose between
# spawning a "2" or a "4".
#
# `sys` lets us cleanly exit the program with sys.exit().
import pygame
import random
import sys


# ========================================================================
# CONSTANTS — TWEAK THESE TO EXPERIMENT!
# ========================================================================
# Constants are values that do not change while the program runs.
# By convention in Python, we write them in ALL_CAPS_WITH_UNDERSCORES.
# Putting them all at the top makes the program much easier to modify:
# you can change the look or feel of the game without hunting through
# the rest of the code.
# ------------------------------------------------------------------------

# ---- Board size ----
# The classic 2048 game uses a 4x4 grid. Try 3 for an easier game,
# or 5 or 6 for a much harder one. The code adjusts automatically!
GRID_SIZE = 4  # Number of cells along one side (so total cells = GRID_SIZE * GRID_SIZE)

# ---- Visual sizing (in pixels) ----
# Each tile is a square. Larger numbers = bigger tiles on screen.
TILE_SIZE = 100              # Width and height of each tile in pixels.
TILE_PADDING = 10            # Space between tiles (and around the edges of the board).
HEADER_HEIGHT = 100           # Space at the top for the score and title.

# We CALCULATE the window size from the values above so everything
# stays nicely aligned even if you change GRID_SIZE or TILE_SIZE.
# Formula: padding + (tile + padding) repeated GRID_SIZE times.
WINDOW_WIDTH = TILE_PADDING + (TILE_SIZE + TILE_PADDING) * GRID_SIZE
WINDOW_HEIGHT = HEADER_HEIGHT + WINDOW_WIDTH  # Square board + header on top.

# ---- Frame rate ----
# How many times per second the screen refreshes. 60 is smooth and standard.
# This game doesn't need a high frame rate since it's turn-based,
# but a steady FPS keeps the window responsive.
FPS = 60

# ---- Game rules ----
# The value tiles must reach to "win". Try 1024 for a quicker win,
# or 4096 if you're feeling ambitious!
WIN_VALUE = 2048

# Probability (between 0.0 and 1.0) that a NEW tile is a "2".
# The rest of the time it will be a "4". The classic game uses 0.9.
# Try lowering it to 0.5 to see how the game changes when more 4s appear.
PROBABILITY_OF_2 = 0.9

# ---- Colors ----
# Colors in Pygame are tuples of three numbers: (Red, Green, Blue),
# each between 0 (none) and 255 (max). Try changing them to make
# your own color scheme!
COLOR_BACKGROUND = (250, 248, 239)   # The window background (cream).
COLOR_BOARD = (187, 173, 160)        # The board behind the tiles (warm gray).
COLOR_EMPTY_CELL = (205, 193, 180)   # Empty cells on the board.
COLOR_TEXT_DARK = (119, 110, 101)    # Used for small numbers (2, 4) and labels.
COLOR_TEXT_LIGHT = (249, 246, 242)   # Used for large numbers (8 and up).
COLOR_OVERLAY = (255, 255, 255)      # White overlay shown on win/lose.

# Each tile value (2, 4, 8, ...) gets its own color. This dictionary
# maps a number to a color tuple. If a value isn't in this dictionary,
# we'll fall back to a default color further down. Try editing these!
TILE_COLORS = {
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149, 99),
    32:   (246, 124, 95),
    64:   (246, 94, 59),
    128:  (237, 207, 114),
    256:  (237, 204, 97),
    512:  (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}
# Color used for tiles whose value isn't listed above (like 4096+).
COLOR_TILE_DEFAULT = (60, 58, 50)


# ========================================================================
# GAME LOGIC FUNCTIONS
# ========================================================================
# These functions know NOTHING about graphics — they just manipulate
# the board (a 2D list of numbers). Keeping the rules of the game
# separate from the visuals is a useful programming habit: it makes
# the logic easier to test and reuse.
# ------------------------------------------------------------------------

def create_empty_board():
    """
    Create a fresh, empty board: a 2D list filled with zeros.
    A "2D list" is a list of lists. Each inner list is one row.
    A 0 means "this cell is empty"; any other number is a tile value.

    Example output for GRID_SIZE = 4:
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]]
    """
    # This is a "list comprehension" — a compact way to build a list.
    # It says: "for each row index, make a list of GRID_SIZE zeros".
    return [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def add_random_tile(board):
    """
    Pick a random empty cell on the board and place a new tile there.
    The new tile is a 2 most of the time, and occasionally a 4.

    The function MODIFIES the board in place — it doesn't return a new one.
    """
    # First, build a list of (row, col) positions that are currently empty.
    empty_cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] == 0:
                empty_cells.append((row, col))

    # If the board is full, there's nothing to do. Just return.
    if not empty_cells:
        return

    # Pick one of the empty cells at random.
    row, col = random.choice(empty_cells)

    # Decide if the new tile should be a 2 or a 4.
    # random.random() returns a float between 0.0 and 1.0.
    if random.random() < PROBABILITY_OF_2:
        board[row][col] = 2
    else:
        board[row][col] = 4


def slide_row_left(row):
    """
    Take ONE row of numbers and slide everything to the left, merging
    equal neighbors. Returns the new row AND how many points were
    earned by merges in this row.

    Example: [2, 2, 4, 0]  -->  [4, 4, 0, 0], score gained = 4
             [0, 2, 0, 2]  -->  [4, 0, 0, 0], score gained = 4
             [4, 4, 4, 4]  -->  [8, 8, 0, 0], score gained = 16

    This is the heart of the 2048 logic! All four directions reuse
    this function — we just rotate the board first (see move() below).
    """
    # Step 1: Remove zeros so all the numbers are packed to the left.
    # `non_zero` is a new list with only the actual tile values.
    non_zero = [value for value in row if value != 0]

    # Step 2: Walk through the packed list and merge neighbors that are equal.
    merged = []
    score_gained = 0
    i = 0
    while i < len(non_zero):
        # Check if the current tile and the next one are equal.
        # The "i + 1 < len(...)" check makes sure we don't go off the end.
        if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
            # Merge! The new tile's value is double the original.
            new_value = non_zero[i] * 2
            merged.append(new_value)
            score_gained += new_value  # Each merge adds the new value to the score.
            i += 2  # Skip BOTH tiles we just merged.
        else:
            # No merge — just keep this tile as-is.
            merged.append(non_zero[i])
            i += 1

    # Step 3: Pad the right side with zeros so the row is the right length again.
    while len(merged) < GRID_SIZE:
        merged.append(0)

    return merged, score_gained


def move(board, direction):
    """
    Slide the entire board in the given direction.
    `direction` should be one of: "left", "right", "up", "down".

    Returns a tuple: (new_board, score_gained, did_anything_move).
    `did_anything_move` is True if the board actually changed —
    we use this to decide whether to spawn a new tile.

    TRICK: We only need to write the "slide left" logic. For the other
    directions, we transform the board so that the desired direction
    BECOMES "left", slide, then transform it back. Nice and tidy!
    """
    # Save a copy of the original board so we can compare at the end
    # to see if anything actually moved. We use a list comprehension
    # to copy each row (a "shallow copy" of each row is fine since
    # rows contain only numbers).
    original = [row[:] for row in board]

    # ---- Step 1: Transform the board so the move becomes "slide left" ----
    if direction == "left":
        working = [row[:] for row in board]
    elif direction == "right":
        # Reverse each row. Sliding the reversed row left is the same
        # as sliding the original row right.
        working = [row[::-1] for row in board]
    elif direction == "up":
        # Transpose: rows become columns. Now "up" looks like "left".
        # zip(*board) is a Python idiom for transposing a 2D list.
        working = [list(row) for row in zip(*board)]
    elif direction == "down":
        # Transpose AND reverse each row.
        working = [list(row)[::-1] for row in zip(*board)]
    else:
        # Unknown direction — do nothing. (Defensive programming!)
        return board, 0, False

    # ---- Step 2: Slide every row to the left, summing up score ----
    total_score_gained = 0
    new_working = []
    for row in working:
        new_row, score_gained = slide_row_left(row)
        new_working.append(new_row)
        total_score_gained += score_gained

    # ---- Step 3: Reverse the transformation from Step 1 ----
    if direction == "left":
        new_board = new_working
    elif direction == "right":
        new_board = [row[::-1] for row in new_working]
    elif direction == "up":
        # Transpose back to undo the original transpose.
        new_board = [list(row) for row in zip(*new_working)]
    elif direction == "down":
        # Un-reverse, then un-transpose.
        un_reversed = [row[::-1] for row in new_working]
        new_board = [list(row) for row in zip(*un_reversed)]

    # ---- Step 4: Did anything actually change? ----
    # We compare the original and new boards. If they're identical,
    # the move was illegal (e.g. pressing left when nothing can slide left).
    did_anything_move = (new_board != original)

    return new_board, total_score_gained, did_anything_move


def has_won(board):
    """Return True if any tile on the board has reached WIN_VALUE."""
    # `any(...)` returns True if AT LEAST ONE element is truthy.
    # Here we generate True/False for each cell and check if any are True.
    return any(
        board[row][col] >= WIN_VALUE
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
    )


def has_lost(board):
    """
    Return True if the board is full AND no moves are possible.
    A move is possible if there's an empty cell, OR if any two
    adjacent cells (horizontally or vertically) have the same value.
    """
    # If there's any empty cell, we haven't lost.
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] == 0:
                return False

    # Check every cell against its right and bottom neighbors for a match.
    # We don't need to check left/up because those are covered by the
    # right/bottom checks of the OTHER cells.
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = board[row][col]
            # Right neighbor (only if it exists).
            if col + 1 < GRID_SIZE and board[row][col + 1] == value:
                return False
            # Bottom neighbor (only if it exists).
            if row + 1 < GRID_SIZE and board[row + 1][col] == value:
                return False

    # Board is full and no merges are possible — game over.
    return True


# ========================================================================
# DRAWING FUNCTIONS
# ========================================================================
# These functions handle everything visual. They take in the current
# game state and draw it to the screen.
# ------------------------------------------------------------------------

def get_tile_color(value):
    """Look up the background color for a tile based on its value."""
    # `dict.get(key, default)` returns the value for `key` if it exists,
    # otherwise returns `default`. Very handy!
    return TILE_COLORS.get(value, COLOR_TILE_DEFAULT)


def get_text_color(value):
    """Small numbers use dark text; larger numbers use light text."""
    # 2 and 4 are light-colored tiles, so we use dark text for contrast.
    if value <= 4:
        return COLOR_TEXT_DARK
    else:
        return COLOR_TEXT_LIGHT


def get_font_size(value):
    """
    Pick a font size that fits the number on the tile.
    Bigger numbers have more digits, so we shrink the font for them.
    """
    if value < 100:        # 1 or 2 digits ("2", "64")
        return 48
    elif value < 1000:     # 3 digits ("128", "512")
        return 40
    elif value < 10000:    # 4 digits ("1024", "2048")
        return 32
    else:                  # 5+ digits — rare but possible!
        return 26


def draw_board(screen, board, score, font_score):
    """Draw the entire game state: header, board background, and tiles."""

    # Fill the whole window with the background color first.
    # This effectively erases the previous frame.
    screen.fill(COLOR_BACKGROUND)

    # ---- Draw the header (title + score) ----
    title_font = pygame.font.SysFont("Arial", 56, bold=True)
    title_surface = title_font.render("2048", True, COLOR_TEXT_DARK)
    # `blit` means "copy this image onto the screen at this position".
    screen.blit(title_surface, (TILE_PADDING, TILE_PADDING))

    score_text = f"Score: {score}"
    score_surface = font_score.render(score_text, True, COLOR_TEXT_DARK)
    # Right-align the score by computing its position from the window width.
    score_rect = score_surface.get_rect()
    score_rect.topright = (WINDOW_WIDTH - TILE_PADDING, TILE_PADDING + 20)
    screen.blit(score_surface, score_rect)

    # ---- Draw the rounded board background behind the tiles ----
    board_rect = pygame.Rect(0, HEADER_HEIGHT, WINDOW_WIDTH, WINDOW_WIDTH)
    pygame.draw.rect(screen, COLOR_BOARD, board_rect)

    # ---- Draw each cell (empty or with a tile) ----
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # Compute the top-left pixel of THIS cell.
            # Each cell occupies (TILE_SIZE + TILE_PADDING) pixels,
            # plus an initial padding offset.
            x = TILE_PADDING + col * (TILE_SIZE + TILE_PADDING)
            y = HEADER_HEIGHT + TILE_PADDING + row * (TILE_SIZE + TILE_PADDING)

            value = board[row][col]
            cell_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            # Choose color based on whether this cell is empty or has a tile.
            if value == 0:
                color = COLOR_EMPTY_CELL
            else:
                color = get_tile_color(value)

            # The `border_radius` argument rounds the corners of the rectangle.
            # Try setting it to 0 for sharp corners!
            pygame.draw.rect(screen, color, cell_rect, border_radius=6)

            # If there's a tile, draw its number centered on the cell.
            if value != 0:
                font_size = get_font_size(value)
                tile_font = pygame.font.SysFont("Arial", font_size, bold=True)
                text_color = get_text_color(value)
                text_surface = tile_font.render(str(value), True, text_color)
                # `get_rect(center=...)` builds a rect centered on a point.
                text_rect = text_surface.get_rect(center=cell_rect.center)
                screen.blit(text_surface, text_rect)


def draw_message_overlay(screen, big_text, small_text):
    """
    Draw a translucent overlay with a big message (e.g. "You Win!")
    and a smaller hint below it. Used for win and game-over screens.
    """
    # Pygame doesn't let us draw a translucent rect directly to the screen,
    # so we make a separate Surface, fill it with a partially transparent
    # color, and then blit it onto the main screen.
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(180)  # 0 = fully transparent, 255 = fully opaque.
    overlay.fill(COLOR_OVERLAY)
    screen.blit(overlay, (0, 0))

    # Draw the big message.
    big_font = pygame.font.SysFont("Arial", 64, bold=True)
    big_surface = big_font.render(big_text, True, COLOR_TEXT_DARK)
    big_rect = big_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
    screen.blit(big_surface, big_rect)

    # Draw the smaller hint below.
    small_font = pygame.font.SysFont("Arial", 24)
    small_surface = small_font.render(small_text, True, COLOR_TEXT_DARK)
    small_rect = small_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
    screen.blit(small_surface, small_rect)


# ========================================================================
# MAIN GAME FUNCTION
# ========================================================================
# This is where everything comes together: setup, the game loop,
# input handling, and drawing.
# ------------------------------------------------------------------------

def main():
    """Run the game! This is the entry point of the program."""

    # ---- Pygame initialization ----
    # pygame.init() boots up all the Pygame subsystems (graphics, fonts, etc).
    # You must call this before doing anything else with Pygame.
    pygame.init()

    # Create the window. The tuple is (width, height) in pixels.
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # The string shown in the window title bar.
    pygame.display.set_caption("2048 — Use arrow keys, R to restart")

    # The Clock keeps the frame rate steady.
    clock = pygame.time.Clock()

    # We pre-create the score font once (instead of every frame) for efficiency.
    font_score = pygame.font.SysFont("Arial", 28, bold=True)

    # ---- Game state setup ----
    # We wrap setup in a small helper so "restart" can call it again.
    def new_game():
        b = create_empty_board()
        # Every game starts with TWO random tiles on the board.
        add_random_tile(b)
        add_random_tile(b)
        return b, 0  # board, score

    board, score = new_game()
    game_over = False  # Becomes True when the player can no longer move.
    won = False        # Becomes True the first time we hit WIN_VALUE.
    # `acknowledged_win` lets the player keep playing past 2048
    # after they've seen the win message once.
    acknowledged_win = False

    # ---- Main game loop ----
    # `running` controls when the game exits. We keep looping until
    # the player closes the window (or presses Escape, etc.).
    running = True
    while running:

        # ---- Handle events (keyboard, mouse, window close, ...) ----
        # Pygame queues up all the things that happened since the last frame.
        # We loop through them and decide how to react to each one.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # The user clicked the window's close button.
                running = False

            elif event.type == pygame.KEYDOWN:
                # A key was just pressed. `event.key` tells us which one.

                # Press R to start a brand new game.
                if event.key == pygame.K_r:
                    board, score = new_game()
                    game_over = False
                    won = False
                    acknowledged_win = False

                # Press Escape to quit.
                elif event.key == pygame.K_ESCAPE:
                    running = False

                # If the game is over, ignore movement keys.
                # (Press R or Escape, as instructed on screen.)
                elif game_over:
                    pass

                # If the user just won and hasn't dismissed the message,
                # any non-restart key dismisses it so they can keep playing.
                elif won and not acknowledged_win:
                    acknowledged_win = True

                else:
                    # Map arrow keys to directions. `direction` stays None
                    # if the key wasn't an arrow key, in which case we ignore it.
                    direction = None
                    if event.key == pygame.K_LEFT:
                        direction = "left"
                    elif event.key == pygame.K_RIGHT:
                        direction = "right"
                    elif event.key == pygame.K_UP:
                        direction = "up"
                    elif event.key == pygame.K_DOWN:
                        direction = "down"

                    if direction is not None:
                        # Try the move. If it actually changes the board,
                        # update the score and spawn a new tile.
                        new_board, gained, moved = move(board, direction)
                        if moved:
                            board = new_board
                            score += gained
                            add_random_tile(board)

                            # Check for win/lose AFTER the new tile appears.
                            if not won and has_won(board):
                                won = True
                            if has_lost(board):
                                game_over = True

        # ---- Draw everything ----
        draw_board(screen, board, score, font_score)

        # If the player won and hasn't dismissed the message yet, show it.
        if won and not acknowledged_win:
            draw_message_overlay(
                screen,
                "You Win!",
                "Press any key to keep going, or R to restart.",
            )
        # If the game is over, show the game-over screen.
        elif game_over:
            draw_message_overlay(
                screen,
                "Game Over",
                "Press R to play again.",
            )

        # `pygame.display.flip()` makes everything we just drew visible.
        # Until we call this, all our drawing is "off-screen".
        pygame.display.flip()

        # Wait just long enough so we don't exceed FPS frames per second.
        clock.tick(FPS)

    # ---- Clean up when the loop ends ----
    pygame.quit()
    sys.exit()


# ========================================================================
# PROGRAM ENTRY POINT
# ========================================================================
# This is a common Python idiom. The code inside the `if` block only
# runs when this file is executed directly (e.g. `python game_2048.py`),
# not when it's imported as a module from another file. It's a good
# habit even for small scripts.
# ------------------------------------------------------------------------
if __name__ == "__main__":
    main()
