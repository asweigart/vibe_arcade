"""
================================================================================
  SIMPLE TETRIS — a beginner-friendly implementation in Python + Pygame
================================================================================

WHAT THIS FILE CONTAINS:
  A complete, playable Tetris game in a single file. No external assets are
  needed (no images, no sound files) — everything is drawn with rectangles
  and text at runtime.

HOW TO RUN:
  1. Make sure you have Python 3.8+ installed.
  2. Install pygame:       pip install pygame
  3. Run the file:         python tetris.py

HOW TO PLAY:
  Left / Right arrows ..... Move the falling piece sideways
  Down arrow .............. Soft-drop (makes it fall faster while held)
  Up arrow or X ........... Rotate clockwise
  Z ....................... Rotate counter-clockwise
  Space ................... Hard-drop (piece slams to the bottom instantly)
  P ....................... Pause / unpause
  R ....................... Restart after game over
  Esc ..................... Quit

HOW THIS CODE IS ORGANIZED (top to bottom):
  1. Imports
  2. CONSTANTS — colors, sizes, speeds. Edit these to tweak the game!
  3. PIECE DEFINITIONS — the seven classic Tetris shapes
  4. HELPER FUNCTIONS — small, focused utilities
  5. GAME STATE — variables that change while playing
  6. GAME LOGIC FUNCTIONS — spawning, moving, rotating, locking, clearing
  7. DRAWING FUNCTIONS — painting the screen each frame
  8. MAIN LOOP — the heartbeat of the program

A NOTE ON COORDINATES:
  The playing field ("board") is a 2D grid. We use (row, column) indexing:
    - row 0 is the TOP of the board
    - row HEIGHT-1 is the BOTTOM
    - column 0 is the LEFT
    - column WIDTH-1 is the RIGHT
  Pieces are also stored as grids of the same shape, so moving a piece is
  just adding an offset to its row/column position.
================================================================================
"""

# ============================================================================
# 1. IMPORTS
# ============================================================================
# `pygame` handles drawing, windowing, and input for us.
# `random` is used to pick which piece comes next.
# `sys` lets us exit cleanly.
# `copy.deepcopy` makes independent copies of piece shapes so rotating one
#   piece does not accidentally modify the template it was copied from.
import pygame
import random
import sys
from copy import deepcopy


# ============================================================================
# 2. CONSTANTS — tweak these to change how the game looks and feels
# ============================================================================
# All "magic numbers" live here so you only have to change them in one place.
# Each group has suggestions for what happens if you change it.

# ---- Board dimensions (in cells, not pixels) -------------------------------
# Classic Tetris is 10 wide and 20 tall. Try 8x16 for a tighter game, or
# 14x24 for something more sprawling.
BOARD_WIDTH = 10          # number of columns
BOARD_HEIGHT = 20         # number of visible rows

# ---- Pixel sizing ----------------------------------------------------------
# CELL_SIZE is how big each grid square is in pixels. Bigger = chunkier look.
# Try 20 for a retro feel, 40 for a more modern, larger display.
CELL_SIZE = 30            # pixels per grid cell

# Extra space around the board for the side panel (score, next piece, etc.)
# and a bit of breathing room at the top/bottom.
SIDE_PANEL_WIDTH = 200    # width of the info panel to the right of the board
MARGIN = 20               # empty space around everything

# The full window size is computed from the values above. You usually won't
# need to edit these two lines directly.
WINDOW_WIDTH = BOARD_WIDTH * CELL_SIZE + SIDE_PANEL_WIDTH + MARGIN * 3
WINDOW_HEIGHT = BOARD_HEIGHT * CELL_SIZE + MARGIN * 2

# ---- Timing / difficulty ---------------------------------------------------
# FPS controls how smoothly the game runs. 60 is a good default. Lower it
# (e.g. 30) on very slow computers.
FPS = 60

# How long (in milliseconds) a piece waits before automatically dropping one
# row. A LOWER number means FASTER falling, which is HARDER.
# Try 1000 for a relaxing pace, 300 for a panic-inducing challenge.
INITIAL_FALL_DELAY_MS = 600

# Every time the player clears this many total lines, the fall delay is
# multiplied by LEVEL_SPEEDUP (so the game gets faster). Set LEVEL_SPEEDUP to
# 1.0 to disable leveling up entirely.
LINES_PER_LEVEL = 10
LEVEL_SPEEDUP = 0.85       # 0.85 = each level is 15% faster than the last
MIN_FALL_DELAY_MS = 80     # the game never gets faster than this

# How often (ms) held left/right/down keys auto-repeat. Lower = more responsive
# but can feel twitchy. 80–120 is a sweet spot.
MOVE_REPEAT_DELAY_MS = 100

# ---- Scoring ---------------------------------------------------------------
# Classic Tetris rewards clearing multiple lines at once. The index is the
# number of lines cleared in a single drop (0..4). Four at once = "Tetris"!
# Feel free to inflate these numbers for more dopamine.
SCORE_PER_LINES = [0, 100, 300, 500, 800]

# Points per cell for soft-drop (holding Down) and hard-drop (Space).
# Hard-drop gives more because it commits you instantly.
SOFT_DROP_POINTS_PER_CELL = 1
HARD_DROP_POINTS_PER_CELL = 2

# ---- Colors (R, G, B) each 0–255 -------------------------------------------
# Change these freely to re-theme the game. Try a pastel palette, or make
# everything grayscale for a minimalist look.
COLOR_BACKGROUND = (15, 15, 25)        # nearly-black with a hint of blue
COLOR_BOARD_BG = (30, 30, 45)          # slightly lighter than background
COLOR_GRID_LINE = (45, 45, 65)         # subtle grid lines inside the board
COLOR_BORDER = (200, 200, 220)         # outline around the play area
COLOR_TEXT = (230, 230, 240)           # primary text color
COLOR_TEXT_DIM = (150, 150, 170)       # secondary / label text
COLOR_GHOST = (80, 80, 100)            # the "preview" of where a piece lands

# One color per piece. Index matches the piece's ID (see PIECES below).
# These are the classic Tetris colors — swap them for your own palette!
PIECE_COLORS = {
    'I': (0, 240, 240),     # cyan
    'O': (240, 240, 0),     # yellow
    'T': (160, 0, 240),     # purple
    'S': (0, 240, 0),       # green
    'Z': (240, 0, 0),       # red
    'J': (0, 0, 240),       # blue
    'L': (240, 160, 0),     # orange
}


# ============================================================================
# 3. PIECE DEFINITIONS
# ============================================================================
# Each piece is represented as a small 2D grid of 0s and 1s. A 1 means "this
# cell is part of the piece," a 0 means "empty space." The piece's grid is
# just big enough to rotate in place.
#
# For example, the T-piece looks like this in its starting rotation:
#     0 1 0
#     1 1 1
#     0 0 0
# Rotating it 90° clockwise gives:
#     0 1 0
#     0 1 1
#     0 1 0
#
# Storing pieces as grids makes rotation a simple, uniform operation (see
# `rotate_shape` below) instead of hand-coding every rotation state.
PIECES = {
    'I': [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    'O': [
        [1, 1],
        [1, 1],
    ],
    'T': [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    'S': [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
    ],
    'Z': [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0],
    ],
    'J': [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ],
    'L': [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0],
    ],
}

# A list of all piece IDs, handy when we want to pick a random one.
PIECE_IDS = list(PIECES.keys())


# ============================================================================
# 4. HELPER FUNCTIONS
# ============================================================================

def make_empty_board():
    """
    Build a fresh, empty board: a 2D list of None values.
    None means "empty cell." When a piece locks into place, we replace the
    None with the piece's color so we can draw it later.
    """
    # This is a "list comprehension" — a compact way to build lists.
    # It creates BOARD_HEIGHT rows, each containing BOARD_WIDTH None values.
    return [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]


def rotate_shape(shape):
    """
    Rotate a 2D shape 90° CLOCKWISE and return the new shape.

    The classic trick: to rotate a matrix 90° clockwise, transpose it
    (swap rows with columns) and then reverse each row.

    Example — rotating the T piece clockwise:
        Before:            After transpose:      After reversing rows:
          0 1 0              0 1 0                 0 1 0
          1 1 1              1 1 0                 0 1 1
          0 0 0              0 1 0                 0 1 0
    """
    # zip(*shape) gives us the columns of `shape` as tuples.
    # list(row) turns each tuple back into a list so we can edit it later.
    transposed = [list(row) for row in zip(*shape)]
    # Reversing each row completes the clockwise rotation.
    return [row[::-1] for row in transposed]


def rotate_shape_ccw(shape):
    """
    Rotate 90° COUNTER-clockwise. The easy way: rotate clockwise three times.
    (Four rotations would bring us back to where we started.)
    """
    return rotate_shape(rotate_shape(rotate_shape(shape)))


def new_piece():
    """
    Create a new falling piece, positioned at the top-center of the board.

    A "piece" is a small dictionary bundling together everything we need to
    know: its ID (like 'T'), its current shape grid, and its position on
    the board (row and column of the shape's top-left corner).
    """
    piece_id = random.choice(PIECE_IDS)
    # deepcopy so that rotating this piece won't mutate the template in PIECES.
    shape = deepcopy(PIECES[piece_id])
    # Center the piece horizontally. Integer division (//) rounds down.
    col = BOARD_WIDTH // 2 - len(shape[0]) // 2
    # Start at the very top. Row 0 is the top row.
    row = 0
    return {
        'id': piece_id,
        'shape': shape,
        'row': row,
        'col': col,
    }


def piece_cells(piece):
    """
    Yield (row, col) positions for every filled cell of the piece,
    translated to board coordinates.

    "Yield" makes this a generator — we can loop over the results without
    building a full list in memory. It's a tidy way to answer the question
    "which board cells does this piece currently occupy?"
    """
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:  # 1 means "filled" for this piece
                yield piece['row'] + r, piece['col'] + c


def is_valid_position(board, piece):
    """
    Return True if the piece's current position is legal:
      - every filled cell must be inside the board bounds
      - every filled cell must not overlap an already-locked block
    Used to check moves/rotations BEFORE we commit to them.
    """
    for r, c in piece_cells(piece):
        # Check horizontal bounds.
        if c < 0 or c >= BOARD_WIDTH:
            return False
        # Check the bottom bound. (We let pieces exist above the top of the
        # board briefly when they first spawn or during rotation.)
        if r >= BOARD_HEIGHT:
            return False
        # Cells above the board (r < 0) are OK — a piece is just spawning.
        if r >= 0 and board[r][c] is not None:
            return False
    return True


# ============================================================================
# 5. GAME STATE
# ============================================================================
# We put all mutable game state inside a single dictionary. This makes it
# easy to reset the game (just build a fresh dictionary) and easy to pass
# the whole state into functions as one argument.

def make_initial_state():
    """Build a brand-new game state — used at startup and on restart."""
    return {
        'board': make_empty_board(),
        'current': new_piece(),      # the piece the player is controlling
        'next': new_piece(),         # shown in the side panel as a preview
        'score': 0,
        'lines_cleared': 0,
        'level': 1,
        'fall_delay_ms': INITIAL_FALL_DELAY_MS,
        'fall_timer_ms': 0,          # accumulates time; when it exceeds
                                     # fall_delay_ms, the piece drops a row
        'game_over': False,
        'paused': False,
    }


# ============================================================================
# 6. GAME LOGIC FUNCTIONS
# ============================================================================

def try_move(state, dr, dc):
    """
    Attempt to move the current piece by (dr rows, dc columns).
    Return True if the move succeeded, False if it was blocked.

    We test the move by temporarily applying it, checking validity, and
    undoing it if it doesn't work. This "look before you leap" approach is
    much simpler than trying to predict collisions mathematically.
    """
    piece = state['current']
    piece['row'] += dr
    piece['col'] += dc
    if is_valid_position(state['board'], piece):
        return True
    # Move was invalid — undo it.
    piece['row'] -= dr
    piece['col'] -= dc
    return False


def try_rotate(state, clockwise=True):
    """
    Attempt to rotate the current piece. Includes simple "wall kicks":
    if the rotated piece would clip into a wall, we try nudging it left
    or right by one or two columns before giving up. This makes rotations
    near the walls feel much more forgiving.
    """
    piece = state['current']
    old_shape = piece['shape']
    piece['shape'] = rotate_shape(old_shape) if clockwise else rotate_shape_ccw(old_shape)

    # Try the rotation as-is, then with small horizontal nudges.
    # The order (0, -1, 1, -2, 2) tries "no kick" first, then left, then
    # right, then bigger kicks. That's enough to handle all basic cases.
    for kick in (0, -1, 1, -2, 2):
        piece['col'] += kick
        if is_valid_position(state['board'], piece):
            return True
        piece['col'] -= kick

    # All kicks failed — undo the rotation.
    piece['shape'] = old_shape
    return False


def lock_piece(state):
    """
    "Freeze" the current piece onto the board. This happens when the piece
    can no longer move down. After locking, we check for completed lines,
    update the score, and spawn the next piece.
    """
    board = state['board']
    piece = state['current']
    color = PIECE_COLORS[piece['id']]

    for r, c in piece_cells(piece):
        # If a piece locks with cells above the top of the board, the player
        # has topped out — game over.
        if r < 0:
            state['game_over'] = True
            return
        board[r][c] = color

    # Remove any completed rows and update the score.
    clear_completed_lines(state)

    # Move the "next" piece into play and generate a new "next" piece.
    state['current'] = state['next']
    state['next'] = new_piece()

    # If the brand-new piece spawns into occupied cells, the board is full.
    if not is_valid_position(board, state['current']):
        state['game_over'] = True


def clear_completed_lines(state):
    """
    Find rows that are completely filled, remove them, and add empty rows
    at the top. Update the score and level accordingly.
    """
    board = state['board']
    # Keep only the rows that have at least one empty cell.
    # A row is "full" when every cell is not None.
    new_board = [row for row in board if any(cell is None for cell in row)]
    lines_cleared = BOARD_HEIGHT - len(new_board)

    if lines_cleared > 0:
        # Prepend empty rows to bring the board back to full height.
        empty_rows = [[None for _ in range(BOARD_WIDTH)]
                      for _ in range(lines_cleared)]
        state['board'] = empty_rows + new_board

        # Classic scoring: more lines at once = exponentially more points.
        state['score'] += SCORE_PER_LINES[lines_cleared]
        state['lines_cleared'] += lines_cleared

        # Leveling up: speed the game up every LINES_PER_LEVEL lines.
        new_level = 1 + state['lines_cleared'] // LINES_PER_LEVEL
        if new_level > state['level']:
            state['level'] = new_level
            # Apply the speedup repeatedly if the player cleared several
            # level thresholds in a single drop (rare but possible).
            state['fall_delay_ms'] = max(
                MIN_FALL_DELAY_MS,
                int(INITIAL_FALL_DELAY_MS * (LEVEL_SPEEDUP ** (new_level - 1)))
            )


def hard_drop(state):
    """
    Slam the piece straight down to the lowest legal position, then lock it.
    Awards bonus points for each cell traveled.
    """
    cells_fallen = 0
    while try_move(state, 1, 0):
        cells_fallen += 1
    state['score'] += cells_fallen * HARD_DROP_POINTS_PER_CELL
    lock_piece(state)
    # Reset the gravity timer so the NEW piece gets a full grace period
    # before it starts falling on its own.
    state['fall_timer_ms'] = 0


def soft_drop(state):
    """
    Move the piece down by one row if possible, awarding a small bonus.
    If it can't move, we lock it — just like natural gravity would.
    """
    if try_move(state, 1, 0):
        state['score'] += SOFT_DROP_POINTS_PER_CELL
    else:
        lock_piece(state)
    state['fall_timer_ms'] = 0


def apply_gravity(state, dt_ms):
    """
    Advance the gravity timer. When it exceeds the fall delay, drop the
    piece by one row (or lock it if it can't move down any further).
    `dt_ms` is the time elapsed since the last frame in milliseconds.
    """
    state['fall_timer_ms'] += dt_ms
    while state['fall_timer_ms'] >= state['fall_delay_ms']:
        state['fall_timer_ms'] -= state['fall_delay_ms']
        if not try_move(state, 1, 0):
            lock_piece(state)
            return  # Stop here: piece locked, new piece in play.


def get_ghost_piece(state):
    """
    Return a copy of the current piece moved down as far as it can go.
    This is drawn as an outline to show the player exactly where a hard
    drop would land. Super helpful for planning!
    """
    ghost = {
        'id': state['current']['id'],
        'shape': state['current']['shape'],  # same shape, no need to copy
        'row': state['current']['row'],
        'col': state['current']['col'],
    }
    # Keep moving the ghost down until we can't.
    while True:
        ghost['row'] += 1
        if not is_valid_position(state['board'], ghost):
            ghost['row'] -= 1
            return ghost


# ============================================================================
# 7. DRAWING FUNCTIONS
# ============================================================================
# These functions paint things on the screen. None of them change game
# state — they only read it. That separation (logic vs. rendering) is a
# really useful habit to develop.

# The top-left pixel where the board starts drawing. Computed once so every
# drawing function can reference the same origin.
BOARD_ORIGIN_X = MARGIN
BOARD_ORIGIN_Y = MARGIN


def draw_cell(surface, row, col, color, filled=True):
    """
    Draw a single cell of the board at the given row/col using the given
    color. If `filled` is False, draws only an outline (used for the ghost).
    """
    x = BOARD_ORIGIN_X + col * CELL_SIZE
    y = BOARD_ORIGIN_Y + row * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    if filled:
        pygame.draw.rect(surface, color, rect)
        # A thin inner border gives each block a subtle "beveled" look.
        pygame.draw.rect(surface, COLOR_BOARD_BG, rect, 1)
    else:
        # Draw just a 2-pixel outline.
        pygame.draw.rect(surface, color, rect, 2)


def draw_board(surface, state):
    """Draw the grid background, the locked blocks, and grid lines."""
    # Board backdrop.
    board_rect = pygame.Rect(
        BOARD_ORIGIN_X, BOARD_ORIGIN_Y,
        BOARD_WIDTH * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE,
    )
    pygame.draw.rect(surface, COLOR_BOARD_BG, board_rect)

    # Locked blocks (the stuff at the bottom of the well).
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            color = state['board'][r][c]
            if color is not None:
                draw_cell(surface, r, c, color)

    # Thin grid lines so the player can count cells easily.
    # Try commenting these out for a cleaner look.
    for c in range(BOARD_WIDTH + 1):
        x = BOARD_ORIGIN_X + c * CELL_SIZE
        pygame.draw.line(
            surface, COLOR_GRID_LINE,
            (x, BOARD_ORIGIN_Y),
            (x, BOARD_ORIGIN_Y + BOARD_HEIGHT * CELL_SIZE),
        )
    for r in range(BOARD_HEIGHT + 1):
        y = BOARD_ORIGIN_Y + r * CELL_SIZE
        pygame.draw.line(
            surface, COLOR_GRID_LINE,
            (BOARD_ORIGIN_X, y),
            (BOARD_ORIGIN_X + BOARD_WIDTH * CELL_SIZE, y),
        )

    # Outline around the board.
    pygame.draw.rect(surface, COLOR_BORDER, board_rect, 2)


def draw_piece(surface, piece, ghost=False):
    """Draw the current falling piece (or its ghost)."""
    color = COLOR_GHOST if ghost else PIECE_COLORS[piece['id']]
    for r, c in piece_cells(piece):
        if r < 0:
            # Skip cells above the visible board (right after spawn).
            continue
        draw_cell(surface, r, c, color, filled=not ghost)


def draw_preview_piece(surface, piece, origin_x, origin_y, label, font):
    """
    Draw a small preview of `piece` (used for "Next") next to a label.
    The piece is drawn on its own mini-canvas, ignoring the board.
    """
    # Draw the label above the preview area.
    label_surface = font.render(label, True, COLOR_TEXT_DIM)
    surface.blit(label_surface, (origin_x, origin_y))

    # Preview cells are a bit smaller than board cells so everything fits.
    preview_cell = CELL_SIZE * 2 // 3
    shape = piece['shape']
    color = PIECE_COLORS[piece['id']]

    # Figure out where the actual filled cells are so we can center the
    # preview (some pieces have empty rows/columns in their grid).
    filled = [(r, c) for r, row in enumerate(shape)
              for c, v in enumerate(row) if v]
    if not filled:
        return
    min_r = min(r for r, _ in filled)
    max_r = max(r for r, _ in filled)
    min_c = min(c for _, c in filled)
    max_c = max(c for _, c in filled)
    piece_w = (max_c - min_c + 1) * preview_cell
    piece_h = (max_r - min_r + 1) * preview_cell

    # Center the piece within a 4x4-cell-ish area below the label.
    area_w = 4 * preview_cell
    area_h = 4 * preview_cell
    area_x = origin_x
    area_y = origin_y + 30  # leave space for the label

    offset_x = area_x + (area_w - piece_w) // 2
    offset_y = area_y + (area_h - piece_h) // 2

    for r, c in filled:
        x = offset_x + (c - min_c) * preview_cell
        y = offset_y + (r - min_r) * preview_cell
        rect = pygame.Rect(x, y, preview_cell, preview_cell)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, COLOR_BOARD_BG, rect, 1)


def draw_side_panel(surface, state, font, small_font):
    """Draw the right-hand info panel: score, level, next piece, controls."""
    panel_x = BOARD_ORIGIN_X + BOARD_WIDTH * CELL_SIZE + MARGIN
    y = BOARD_ORIGIN_Y

    # --- Score ---
    score_label = small_font.render("SCORE", True, COLOR_TEXT_DIM)
    surface.blit(score_label, (panel_x, y))
    score_value = font.render(str(state['score']), True, COLOR_TEXT)
    surface.blit(score_value, (panel_x, y + 20))
    y += 70

    # --- Level ---
    level_label = small_font.render("LEVEL", True, COLOR_TEXT_DIM)
    surface.blit(level_label, (panel_x, y))
    level_value = font.render(str(state['level']), True, COLOR_TEXT)
    surface.blit(level_value, (panel_x, y + 20))
    y += 70

    # --- Lines cleared ---
    lines_label = small_font.render("LINES", True, COLOR_TEXT_DIM)
    surface.blit(lines_label, (panel_x, y))
    lines_value = font.render(str(state['lines_cleared']), True, COLOR_TEXT)
    surface.blit(lines_value, (panel_x, y + 20))
    y += 70

    # --- Next piece preview ---
    draw_preview_piece(surface, state['next'], panel_x, y, "NEXT", small_font)
    y += 120

    # --- Controls reminder (helpful for a first-time player) ---
    # A list of (label, key) pairs — easy to edit if you rebind things.
    controls = [
        ("Move",        "< >"),
        ("Soft drop",   "v"),
        ("Rotate",      "^ / X"),
        ("Rotate CCW",  "Z"),
        ("Hard drop",   "Space"),
        ("Pause",       "P"),
        ("Restart",     "R"),
    ]
    for label, key in controls:
        text = small_font.render(f"{label:<10} {key}", True, COLOR_TEXT_DIM)
        surface.blit(text, (panel_x, y))
        y += 18


def draw_center_message(surface, big_font, small_font, title, subtitle=None):
    """Draw a big centered message, optionally with a smaller subtitle."""
    # Semi-transparent veil so the message pops against the busy board.
    veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 160))  # last value is alpha (0–255)
    surface.blit(veil, (0, 0))

    title_surface = big_font.render(title, True, COLOR_TEXT)
    title_rect = title_surface.get_rect(
        center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)
    )
    surface.blit(title_surface, title_rect)

    if subtitle:
        sub_surface = small_font.render(subtitle, True, COLOR_TEXT_DIM)
        sub_rect = sub_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)
        )
        surface.blit(sub_surface, sub_rect)


# ============================================================================
# 8. MAIN LOOP
# ============================================================================

def main():
    """Set up pygame, then run the game loop until the player quits."""
    pygame.init()
    pygame.display.set_caption("Simple Tetris")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # `pygame.font.SysFont(None, ...)` uses the default system font, so we
    # don't need any .ttf files. The numbers are sizes in points.
    big_font = pygame.font.SysFont(None, 56)
    font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 18)

    state = make_initial_state()

    # For auto-repeating movement when the player holds a key. We track the
    # time since each action was last performed. Set to None when the key
    # is not held.
    move_repeat_timers = {'left': None, 'right': None, 'down': None}

    # ---- Main loop ---------------------------------------------------------
    # This runs roughly FPS times per second. Each iteration:
    #   1. Figure out how much time passed since the last iteration (`dt`).
    #   2. Handle input events (key presses, window close).
    #   3. Update game state (gravity, auto-repeat movement).
    #   4. Draw everything to the screen.
    # This "input → update → draw" pattern is the backbone of almost every
    # video game.
    while True:
        dt = clock.tick(FPS)  # ms since last frame, also caps frame rate

        # ---------- 2. EVENTS ----------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the window's close button.
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                # Keys that work no matter what the game state is:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and state['game_over']:
                    state = make_initial_state()
                    move_repeat_timers = {'left': None, 'right': None, 'down': None}
                    continue
                if event.key == pygame.K_p and not state['game_over']:
                    state['paused'] = not state['paused']
                    continue

                # Gameplay keys only work while actively playing:
                if state['game_over'] or state['paused']:
                    continue

                if event.key == pygame.K_LEFT:
                    try_move(state, 0, -1)
                    move_repeat_timers['left'] = 0
                elif event.key == pygame.K_RIGHT:
                    try_move(state, 0, 1)
                    move_repeat_timers['right'] = 0
                elif event.key == pygame.K_DOWN:
                    soft_drop(state)
                    move_repeat_timers['down'] = 0
                elif event.key in (pygame.K_UP, pygame.K_x):
                    try_rotate(state, clockwise=True)
                elif event.key == pygame.K_z:
                    try_rotate(state, clockwise=False)
                elif event.key == pygame.K_SPACE:
                    hard_drop(state)

            elif event.type == pygame.KEYUP:
                # When the player releases a movement key, stop auto-repeating.
                if event.key == pygame.K_LEFT:
                    move_repeat_timers['left'] = None
                elif event.key == pygame.K_RIGHT:
                    move_repeat_timers['right'] = None
                elif event.key == pygame.K_DOWN:
                    move_repeat_timers['down'] = None

        # ---------- 3. UPDATE ----------------------------------------------
        if not state['game_over'] and not state['paused']:
            # Handle held keys: repeat the move every MOVE_REPEAT_DELAY_MS.
            for direction, timer in list(move_repeat_timers.items()):
                if timer is None:
                    continue
                timer += dt
                if timer >= MOVE_REPEAT_DELAY_MS:
                    timer -= MOVE_REPEAT_DELAY_MS
                    if direction == 'left':
                        try_move(state, 0, -1)
                    elif direction == 'right':
                        try_move(state, 0, 1)
                    elif direction == 'down':
                        soft_drop(state)
                move_repeat_timers[direction] = timer

            # Natural gravity.
            apply_gravity(state, dt)

        # ---------- 4. DRAW ------------------------------------------------
        screen.fill(COLOR_BACKGROUND)
        draw_board(screen, state)

        # Draw the ghost first (behind the actual piece) so the real piece
        # covers it if they overlap.
        if not state['game_over']:
            ghost = get_ghost_piece(state)
            draw_piece(screen, ghost, ghost=True)
            draw_piece(screen, state['current'])

        draw_side_panel(screen, state, font, small_font)

        if state['game_over']:
            draw_center_message(
                screen, big_font, small_font,
                "GAME OVER", "Press R to restart, Esc to quit",
            )
        elif state['paused']:
            draw_center_message(
                screen, big_font, small_font,
                "PAUSED", "Press P to resume",
            )

        # Swap the off-screen buffer onto the visible window. Without this
        # call, nothing you drew would actually appear!
        pygame.display.flip()


# This idiom means "only run main() if this file is executed directly,
# not if it's imported as a module." It's a Python convention worth knowing.
if __name__ == "__main__":
    main()
