"""
===============================================================================
  15-TILE SLIDE PUZZLE GAME
===============================================================================

  A classic sliding puzzle game built with Pygame. The goal is to arrange
  the numbered tiles in order (1-15) by sliding them into the empty space.

  HOW TO PLAY:
    - Click on any tile adjacent to the empty space to slide it
    - Or use the ARROW KEYS to slide tiles (arrow direction = direction the
      empty space appears to move)
    - Press 'R' to shuffle and start a new game
    - Press 'ESC' to quit

  HOW TO RUN:
    1. Make sure Python 3 is installed
    2. Install pygame:  pip install pygame
    3. Run:             python slide_puzzle.py

  This file is heavily commented to help beginner programmers understand
  how each part works. Look for the CONSTANTS section near the top — you
  can change those values to experiment with how the game looks and feels!
===============================================================================
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
# 'pygame' is the library that handles graphics, input, and the game window.
# 'random' lets us shuffle the tiles so every game is different.
# 'sys' gives us a clean way to exit the program.
import pygame
import random
import sys


# =============================================================================
# CONSTANTS — Change these to customize the game!
# =============================================================================
# Constants are values that don't change while the program runs. By convention
# in Python, they're written in ALL_CAPS so you can spot them easily. Grouping
# them at the top makes it easy to tweak the game without hunting through code.

# -----------------------------------------------------------------------------
# GRID SETTINGS
# -----------------------------------------------------------------------------
# GRID_SIZE controls how many tiles per row/column.
#   4 = classic 15-puzzle (4x4 grid with 15 tiles + 1 empty space)
#   3 = easier 8-puzzle (3x3 grid with 8 tiles + 1 empty space)
#   5 = harder 24-puzzle (5x5 grid)
# Try changing this to 3 if the 15-puzzle feels too hard!
GRID_SIZE = 4

# TILE_SIZE is how many pixels wide/tall each tile is on screen.
# Bigger = bigger tiles and a bigger window. Try 80 for a smaller window,
# or 150 for a huge one.
TILE_SIZE = 120

# TILE_MARGIN is the gap between tiles in pixels. Set to 0 for tiles that
# touch each other, or try 8 for a more spread-out look.
TILE_MARGIN = 4

# BOARD_PADDING is the space between the board edge and the window edge.
BOARD_PADDING = 20

# -----------------------------------------------------------------------------
# UI (USER INTERFACE) SETTINGS
# -----------------------------------------------------------------------------
# Height of the area above the board where we show the move counter and hints.
UI_HEIGHT = 80

# Size of the text fonts, in pixels.
FONT_SIZE_TILE = 48   # Size of the numbers drawn on tiles
FONT_SIZE_UI = 24     # Size of the UI text (move counter, etc.)
FONT_SIZE_WIN = 56    # Size of the "You won!" message

# -----------------------------------------------------------------------------
# COLORS — stored as (Red, Green, Blue) tuples, each value from 0 to 255
# -----------------------------------------------------------------------------
# Try picking your own colors! A quick way: search "color picker" online
# and copy the RGB values. Each number is 0 (none) to 255 (maximum).

COLOR_BACKGROUND = (30, 30, 40)          # Dark blue-gray — the window background
COLOR_BOARD      = (20, 20, 30)          # Even darker — the board behind tiles
COLOR_TILE       = (70, 130, 200)        # Blue — the normal tile color
COLOR_TILE_HOVER = (90, 160, 230)        # Lighter blue — when mouse hovers a movable tile
COLOR_TILE_SOLVED= (80, 180, 120)        # Green — shown when the puzzle is solved
COLOR_TILE_TEXT  = (255, 255, 255)       # White — the numbers on the tiles
COLOR_EMPTY      = (50, 50, 60)          # Dark — the empty slot
COLOR_UI_TEXT    = (230, 230, 230)       # Light gray — the UI text
COLOR_WIN_TEXT   = (255, 215, 0)         # Gold — the "You won!" message

# -----------------------------------------------------------------------------
# GAMEPLAY SETTINGS
# -----------------------------------------------------------------------------
# How many random moves to make when shuffling. More moves = harder puzzle.
# We shuffle by making random legal moves (instead of placing tiles randomly)
# so the puzzle is GUARANTEED to be solvable. About 100-500 works well.
SHUFFLE_MOVES = 200

# Frames per second — how often the screen redraws. 60 is smooth; 30 is fine
# for a puzzle game. Higher uses more CPU.
FPS = 60

# -----------------------------------------------------------------------------
# DERIVED VALUES — calculated from the constants above. Don't edit these
# directly; change the constants above instead and these will update.
# -----------------------------------------------------------------------------
# Total board dimensions in pixels (tiles + margins between them).
BOARD_PIXELS = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * TILE_MARGIN

# Full window size: board plus padding on both sides, plus UI area on top.
WINDOW_WIDTH = BOARD_PIXELS + BOARD_PADDING * 2
WINDOW_HEIGHT = BOARD_PIXELS + BOARD_PADDING * 2 + UI_HEIGHT

# Pixel coordinates of the board's top-left corner (below the UI area).
BOARD_X = BOARD_PADDING
BOARD_Y = UI_HEIGHT + BOARD_PADDING

# Total number of tiles on the board (including the empty slot).
# For a 4x4 grid that's 16 slots: tiles numbered 1-15 plus one empty.
TOTAL_SLOTS = GRID_SIZE * GRID_SIZE

# We use 0 to represent the empty slot in our board data.
EMPTY_TILE = 0


# =============================================================================
# BOARD LOGIC — functions that handle the puzzle's data and rules
# =============================================================================
# The board is stored as a 2D list (a list of lists). Each inner list is a row.
# For example, a solved 3x3 board looks like this:
#     [[1, 2, 3],
#      [4, 5, 6],
#      [7, 8, 0]]
# The 0 represents the empty slot.

def create_solved_board():
    """
    Creates and returns a board in the solved state: numbers 1 through N-1
    in order, with 0 (the empty slot) in the bottom-right corner.

    A 'list comprehension' is used here — it's a compact way to build a list.
    """
    # Build a flat list [1, 2, 3, ..., N-1, 0]
    numbers = list(range(1, TOTAL_SLOTS)) + [EMPTY_TILE]

    # Split the flat list into rows of length GRID_SIZE.
    # For GRID_SIZE=4, this gives us 4 rows of 4 numbers each.
    board = []
    for row_index in range(GRID_SIZE):
        start = row_index * GRID_SIZE
        end = start + GRID_SIZE
        board.append(numbers[start:end])
    return board


def find_empty(board):
    """
    Returns the (row, column) position of the empty slot on the board.
    We need this often because only tiles next to the empty slot can move.
    """
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] == EMPTY_TILE:
                return row, col
    # This should never happen on a valid board, but return a safe default.
    return 0, 0


def get_movable_positions(board):
    """
    Returns a list of (row, col) positions of tiles that can currently move.
    A tile can move only if it's directly next to the empty slot (up, down,
    left, or right — NOT diagonally).
    """
    empty_row, empty_col = find_empty(board)
    movable = []

    # The four neighbors of the empty slot: up, down, left, right.
    # Each pair is (row_offset, column_offset).
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for row_offset, col_offset in neighbors:
        neighbor_row = empty_row + row_offset
        neighbor_col = empty_col + col_offset
        # Only count positions that are actually on the board.
        if 0 <= neighbor_row < GRID_SIZE and 0 <= neighbor_col < GRID_SIZE:
            movable.append((neighbor_row, neighbor_col))

    return movable


def try_move_tile(board, row, col):
    """
    Attempts to slide the tile at (row, col) into the empty slot.
    Returns True if the move happened, False if the tile couldn't move.

    The board is modified IN PLACE — that means we change the existing list
    rather than creating a new one. (This is why we don't need to return it.)
    """
    # Find where the empty slot is right now.
    empty_row, empty_col = find_empty(board)

    # Calculate how far the clicked tile is from the empty slot.
    row_distance = abs(row - empty_row)
    col_distance = abs(col - empty_col)

    # A tile can move only if it's exactly one step away, either horizontally
    # or vertically (not diagonally). That means one distance is 1 and the
    # other is 0. We can check this with: distances sum to 1.
    if row_distance + col_distance != 1:
        return False

    # Swap the clicked tile with the empty slot.
    # In Python, "a, b = b, a" swaps two values in a single line.
    board[empty_row][empty_col] = board[row][col]
    board[row][col] = EMPTY_TILE
    return True


def shuffle_board(board, num_moves):
    """
    Shuffles the board by making 'num_moves' random legal moves from the
    solved state. Doing it this way guarantees the puzzle is solvable
    (whereas randomly placing tiles could produce an impossible puzzle).
    """
    last_moved = None  # Track the last tile moved to avoid undoing the move

    for _ in range(num_moves):
        # Find all tiles that could move right now.
        options = get_movable_positions(board)

        # Filter out the last-moved tile so we don't immediately undo our
        # previous move (which would waste a shuffle step).
        if last_moved is not None:
            filtered = [pos for pos in options if pos != last_moved]
            # Only use the filter if it still leaves us choices.
            if filtered:
                options = filtered

        # Pick a random movable tile and slide it.
        chosen = random.choice(options)
        empty_before = find_empty(board)
        try_move_tile(board, chosen[0], chosen[1])
        # The chosen tile is now where the empty slot used to be.
        last_moved = empty_before


def is_solved(board):
    """
    Returns True if the board is in the solved state (1, 2, 3, ... with 0
    in the bottom-right corner).
    """
    expected = 1  # The number we expect in the current slot
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # The last slot should be the empty one (0).
            if row == GRID_SIZE - 1 and col == GRID_SIZE - 1:
                if board[row][col] != EMPTY_TILE:
                    return False
            else:
                if board[row][col] != expected:
                    return False
                expected += 1
    return True


# =============================================================================
# DRAWING FUNCTIONS — functions that paint things on the screen
# =============================================================================

def tile_pixel_position(row, col):
    """
    Converts a board position (row, col) into screen pixel coordinates (x, y)
    for the top-left corner of that tile. This is where drawing + clicking
    gets translated between 'game logic' and 'screen pixels'.
    """
    x = BOARD_X + TILE_MARGIN + col * (TILE_SIZE + TILE_MARGIN)
    y = BOARD_Y + TILE_MARGIN + row * (TILE_SIZE + TILE_MARGIN)
    return x, y


def pixel_to_tile(mouse_x, mouse_y):
    """
    Converts screen pixel coordinates (like a mouse click) into a board
    position (row, col). Returns None if the click wasn't on a tile.
    """
    # First check: is the click even inside the board area?
    if mouse_x < BOARD_X or mouse_y < BOARD_Y:
        return None
    if mouse_x >= BOARD_X + BOARD_PIXELS or mouse_y >= BOARD_Y + BOARD_PIXELS:
        return None

    # Figure out which column and row the mouse is over. We use integer
    # division (//) to drop the fractional part.
    col = (mouse_x - BOARD_X - TILE_MARGIN) // (TILE_SIZE + TILE_MARGIN)
    row = (mouse_y - BOARD_Y - TILE_MARGIN) // (TILE_SIZE + TILE_MARGIN)

    # The math above could give a value just outside the grid if the click
    # landed in a margin. Clamp to valid range and return None if out of bounds.
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return int(row), int(col)
    return None


def draw_board(screen, board, font_tile, mouse_pos, solved):
    """
    Draws the entire board: the background rectangle, each tile, and the
    numbers on the tiles. Tiles that can currently be moved light up when
    the mouse hovers over them (unless the puzzle is already solved).
    """
    # Draw the dark rectangle behind the tiles (the "board").
    board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_PIXELS, BOARD_PIXELS)
    pygame.draw.rect(screen, COLOR_BOARD, board_rect)

    # Figure out which tile (if any) the mouse is hovering over.
    # This is only relevant if the puzzle isn't solved yet.
    hovered_tile = pixel_to_tile(*mouse_pos) if not solved else None
    movable = get_movable_positions(board) if not solved else []

    # Loop through every cell in the grid and draw its tile.
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = board[row][col]
            x, y = tile_pixel_position(row, col)
            tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            if value == EMPTY_TILE:
                # Draw the empty slot as a simple dark square.
                pygame.draw.rect(screen, COLOR_EMPTY, tile_rect)
            else:
                # Pick the tile color. Priority:
                #   1. Solved: everything green
                #   2. Hovered AND movable: highlight color
                #   3. Otherwise: normal tile color
                if solved:
                    color = COLOR_TILE_SOLVED
                elif hovered_tile == (row, col) and (row, col) in movable:
                    color = COLOR_TILE_HOVER
                else:
                    color = COLOR_TILE

                # Draw the tile rectangle with slightly rounded corners.
                # 'border_radius' makes the corners nicely rounded.
                pygame.draw.rect(screen, color, tile_rect, border_radius=8)

                # Render the tile's number as text.
                # 'render' returns a small image we can paste onto the screen.
                text_surface = font_tile.render(str(value), True, COLOR_TILE_TEXT)
                # Center the text on the tile.
                text_rect = text_surface.get_rect(center=tile_rect.center)
                screen.blit(text_surface, text_rect)


def draw_ui(screen, font_ui, font_win, moves, solved):
    """
    Draws the UI area at the top of the window: the move counter, a hint
    about controls, and (if solved) a big "You won!" message.
    """
    # Draw the move counter in the top-left of the UI area.
    moves_text = f"Moves: {moves}"
    moves_surface = font_ui.render(moves_text, True, COLOR_UI_TEXT)
    screen.blit(moves_surface, (BOARD_PADDING, 15))

    # Draw a control hint in the top-right.
    hint_text = "R = Shuffle   ESC = Quit"
    hint_surface = font_ui.render(hint_text, True, COLOR_UI_TEXT)
    # Position it so the right edge lines up with the board's right edge.
    hint_rect = hint_surface.get_rect()
    hint_rect.topright = (WINDOW_WIDTH - BOARD_PADDING, 15)
    screen.blit(hint_surface, hint_rect)

    # If the puzzle is solved, draw a celebratory message centered below.
    if solved:
        win_surface = font_win.render("You Won!", True, COLOR_WIN_TEXT)
        win_rect = win_surface.get_rect(center=(WINDOW_WIDTH // 2, 50))
        screen.blit(win_surface, win_rect)
    else:
        # Otherwise, show a subtle second-line hint about how to play.
        controls_surface = font_ui.render(
            "Click a tile or use arrow keys",
            True,
            COLOR_UI_TEXT,
        )
        controls_rect = controls_surface.get_rect(center=(WINDOW_WIDTH // 2, 50))
        screen.blit(controls_surface, controls_rect)


# =============================================================================
# INPUT HANDLING
# =============================================================================

def handle_arrow_key(board, key):
    """
    Handles arrow key presses. Convention: the arrow key indicates the
    direction the EMPTY SLOT moves (equivalently: the tile slides the
    opposite way). So pressing UP slides the tile BELOW the empty slot up
    into the empty slot. This feels natural to most players.

    Returns True if a tile was moved, False otherwise.
    """
    empty_row, empty_col = find_empty(board)

    # Each arrow maps to the position of the tile that should move.
    # For UP arrow: empty slot goes up, so the tile BELOW it moves up.
    if key == pygame.K_UP:
        target = (empty_row + 1, empty_col)
    elif key == pygame.K_DOWN:
        target = (empty_row - 1, empty_col)
    elif key == pygame.K_LEFT:
        target = (empty_row, empty_col + 1)
    elif key == pygame.K_RIGHT:
        target = (empty_row, empty_col - 1)
    else:
        return False

    # Check the target is within the board, then try to move it.
    t_row, t_col = target
    if 0 <= t_row < GRID_SIZE and 0 <= t_col < GRID_SIZE:
        return try_move_tile(board, t_row, t_col)
    return False


# =============================================================================
# MAIN GAME FUNCTION
# =============================================================================

def main():
    """
    The main entry point. Sets up pygame, creates the board, and runs the
    game loop that handles events, updates state, and redraws the screen.
    """
    # ---- SETUP ----
    pygame.init()  # Initialize all of pygame's subsystems (graphics, etc.)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"{TOTAL_SLOTS - 1}-Tile Slide Puzzle")

    # A Clock helps us control the frame rate (how fast the game loop runs).
    clock = pygame.time.Clock()

    # Create the fonts we'll use. 'None' means "use pygame's default font",
    # which avoids needing any external files.
    font_tile = pygame.font.SysFont(None, FONT_SIZE_TILE, bold=True)
    font_ui = pygame.font.SysFont(None, FONT_SIZE_UI)
    font_win = pygame.font.SysFont(None, FONT_SIZE_WIN, bold=True)

    # Create the board and shuffle it so we start with a real puzzle.
    board = create_solved_board()
    shuffle_board(board, SHUFFLE_MOVES)

    # 'moves' counts how many moves the player has made this round.
    moves = 0

    # ---- MAIN GAME LOOP ----
    # This loop runs over and over, ~FPS times per second. On each iteration
    # it handles input, updates the game, and redraws the screen. This is
    # the fundamental pattern for almost every game.
    running = True
    while running:
        # 'pygame.event.get()' returns a list of all new events since last
        # frame — things like mouse clicks and key presses.
        for event in pygame.event.get():

            # The user closed the window (clicked the X button).
            if event.type == pygame.QUIT:
                running = False

            # A key was pressed down.
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Reshuffle and reset move counter.
                    board = create_solved_board()
                    shuffle_board(board, SHUFFLE_MOVES)
                    moves = 0
                elif not is_solved(board):
                    # Arrow keys only work while the puzzle is unsolved.
                    if handle_arrow_key(board, event.key):
                        moves += 1

            # A mouse button was pressed down.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # event.button == 1 means the LEFT mouse button.
                if event.button == 1 and not is_solved(board):
                    clicked = pixel_to_tile(*event.pos)
                    if clicked is not None:
                        row, col = clicked
                        # Try to move the clicked tile. Count the move only
                        # if the tile actually slid.
                        if try_move_tile(board, row, col):
                            moves += 1

        # ---- DRAWING ----
        # Every frame, we re-paint the whole screen from scratch. Start by
        # filling the background, then draw everything on top of it.
        screen.fill(COLOR_BACKGROUND)

        solved = is_solved(board)
        mouse_pos = pygame.mouse.get_pos()

        draw_board(screen, board, font_tile, mouse_pos, solved)
        draw_ui(screen, font_ui, font_win, moves, solved)

        # 'flip' shows everything we just drew. Without this, the screen
        # would appear blank — drawing happens on a hidden buffer first.
        pygame.display.flip()

        # Wait just long enough to keep the loop running at FPS frames/sec.
        clock.tick(FPS)

    # ---- CLEANUP ----
    # Outside the loop means the player quit. Shut down pygame cleanly.
    pygame.quit()
    sys.exit()


# This special check means: "Only run main() if this file was launched
# directly (not imported as a module by some other program)." It's a
# standard Python idiom you'll see in nearly every script.
if __name__ == "__main__":
    main()
