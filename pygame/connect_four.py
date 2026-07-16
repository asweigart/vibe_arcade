"""
=============================================================================
CONNECT FOUR - A Simple Pygame Implementation
=============================================================================

A classic two-player Connect Four game. Players take turns dropping colored
discs into a 7-column, 6-row grid. The first player to connect four of their
discs in a row (horizontally, vertically, or diagonally) wins!

HOW TO PLAY:
    - Player 1 (Red) goes first, then Player 2 (Yellow) alternates.
    - Move your mouse across the top of the board to aim.
    - Click to drop a disc into the selected column.
    - Press 'R' to restart after a game ends.
    - Press 'ESC' or close the window to quit.

REQUIREMENTS:
    - Python 3.6+
    - pygame (install with: pip install pygame)

TO RUN:
    python connect_four.py

=============================================================================
"""

import sys       # Used to cleanly exit the program
import pygame    # The game library that handles graphics, input, and sound


# =============================================================================
# GAME CONSTANTS
# =============================================================================
# Constants are values that never change while the program runs.
# Putting them at the top makes it easy to tweak the game without digging
# through code. Try changing these values to customize the game!
# =============================================================================

# --- Board Dimensions ---
# The classic Connect Four board is 7 columns wide by 6 rows tall.
# Try: COLUMN_COUNT = 8, ROW_COUNT = 7 for a larger board (harder to win).
# Note: you may need to increase WIN_LENGTH if you make the board much larger.
COLUMN_COUNT = 7  # Number of columns (vertical stacks) on the board
ROW_COUNT = 6     # Number of rows (horizontal tiers) on the board

# --- Winning Condition ---
# How many discs in a row are needed to win.
# Try: WIN_LENGTH = 3 for a faster, easier game (like Tic-Tac-Toe).
# Try: WIN_LENGTH = 5 for a much harder challenge.
WIN_LENGTH = 4

# --- Visual Sizes (in pixels) ---
# SQUARE_SIZE is the width/height of one cell on the board.
# Larger values = bigger window and discs. Smaller = more compact.
# Try: SQUARE_SIZE = 80 for a smaller window, or 120 for a bigger one.
SQUARE_SIZE = 100

# Radius of each disc. It should be a bit smaller than SQUARE_SIZE / 2
# so that discs have a nice gap between them.
# Try: DISC_RADIUS = SQUARE_SIZE // 2 - 10 for smaller discs with more spacing.
DISC_RADIUS = SQUARE_SIZE // 2 - 5

# The top row of the window is reserved for showing the "hovering" disc
# that follows the mouse before a player drops it. We use one SQUARE_SIZE
# of vertical space for this preview area.
# Try: setting this to 0 removes the preview area entirely (not recommended).
PREVIEW_HEIGHT = SQUARE_SIZE

# --- Window Size (calculated from the constants above) ---
# We compute these from the board size so the window always fits perfectly.
# You usually shouldn't change these directly — change SQUARE_SIZE instead.
WINDOW_WIDTH = COLUMN_COUNT * SQUARE_SIZE
WINDOW_HEIGHT = (ROW_COUNT * SQUARE_SIZE) + PREVIEW_HEIGHT

# --- Colors (as RGB tuples: Red, Green, Blue, each 0-255) ---
# Feel free to experiment! Pick any colors you like.
# Try a dark-mode theme: BOARD_COLOR = (40, 40, 60), BACKGROUND_COLOR = (20, 20, 30)
BACKGROUND_COLOR = (0, 0, 0)          # Black — shows behind/above the board
BOARD_COLOR = (30, 80, 200)           # Blue — the board itself
EMPTY_SLOT_COLOR = (20, 20, 30)       # Very dark — empty circular holes in the board
PLAYER_1_COLOR = (220, 50, 50)        # Red — Player 1's discs
PLAYER_2_COLOR = (240, 220, 60)       # Yellow — Player 2's discs
TEXT_COLOR = (255, 255, 255)          # White — used for on-screen messages
WIN_HIGHLIGHT_COLOR = (255, 255, 255) # White circle outline around winning discs

# --- Player Identifiers ---
# These are just numbers we store in the board grid to mark which player
# (if any) occupies a cell. EMPTY = 0 means no disc has been played there.
EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2

# --- Frame Rate ---
# How many times per second the game updates. 60 is smooth and standard.
# Try: 30 for a slower-feeling game, or 120 for ultra-smooth motion.
FPS = 60

# --- Font Sizes (in pixels) ---
# Used for on-screen messages like "Player 1 wins!" and "Press R to restart".
# Try: larger values for bigger, more dramatic text.
TITLE_FONT_SIZE = 60
INFO_FONT_SIZE = 28


# =============================================================================
# BOARD LOGIC FUNCTIONS
# =============================================================================
# These functions manage the game state — the 2D grid representing the board.
# We use a list of lists, where board[row][col] stores which player (if any)
# has a disc in that cell. Row 0 is the TOP of the board, row ROW_COUNT-1
# is the BOTTOM (where discs settle first due to "gravity").
# =============================================================================

def create_empty_board():
    """
    Create and return a fresh, empty game board.
    The board is a 2D list: rows (vertical) by columns (horizontal).
    Every cell starts as EMPTY (0).
    """
    # This uses a "list comprehension" — a compact way to create a list.
    # It says: "for each row, make a list of COLUMN_COUNT zeros".
    return [[EMPTY for _ in range(COLUMN_COUNT)] for _ in range(ROW_COUNT)]


def is_column_valid(board, column):
    """
    Check whether a disc can be dropped into the given column.
    Returns True if the column has at least one empty space, False otherwise.
    A column is "full" when its TOP cell (row 0) is no longer EMPTY.
    """
    # First, make sure the column number is in range. Defensive programming!
    if column < 0 or column >= COLUMN_COUNT:
        return False
    # If the top cell is empty, there's still room to drop a disc.
    return board[0][column] == EMPTY


def get_next_open_row(board, column):
    """
    Find the lowest empty row in the given column — this is where a
    dropped disc will land due to simulated gravity.
    Returns the row index, or None if the column is full.
    """
    # Loop from the BOTTOM of the board upward. The first empty cell we
    # find is where the disc will land.
    # range(start, stop, step): start at the last row, go to -1 (exclusive),
    # stepping by -1 (backwards).
    for row in range(ROW_COUNT - 1, -1, -1):
        if board[row][column] == EMPTY:
            return row
    # If we got here, every cell in the column was filled.
    return None


def drop_disc(board, row, column, player):
    """
    Place a player's disc at the specified row and column.
    This modifies the board in place (no need to return it).
    """
    board[row][column] = player


def check_for_win(board, player):
    """
    Check if the given player has WIN_LENGTH discs in a row somewhere.
    Returns a list of (row, column) tuples for the winning discs if found,
    or None if there's no win yet.

    We check four possible directions for a winning line:
      1. Horizontal   (→)
      2. Vertical     (↓)
      3. Diagonal down-right (↘)
      4. Diagonal up-right   (↗)
    """

    # --- 1. HORIZONTAL CHECK ---
    # For each row, slide a window of WIN_LENGTH cells across from left to right.
    # The "- WIN_LENGTH + 1" ensures we don't go off the right edge of the board.
    for row in range(ROW_COUNT):
        for col in range(COLUMN_COUNT - WIN_LENGTH + 1):
            # Collect the cells in this horizontal window
            window = [(row, col + offset) for offset in range(WIN_LENGTH)]
            # Check if ALL cells in the window belong to this player
            if all(board[r][c] == player for r, c in window):
                return window  # Found a win! Return the winning cells.

    # --- 2. VERTICAL CHECK ---
    # For each column, slide a window downward.
    for col in range(COLUMN_COUNT):
        for row in range(ROW_COUNT - WIN_LENGTH + 1):
            window = [(row + offset, col) for offset in range(WIN_LENGTH)]
            if all(board[r][c] == player for r, c in window):
                return window

    # --- 3. DIAGONAL DOWN-RIGHT CHECK (↘) ---
    # Starting positions must leave enough room both right AND down.
    for row in range(ROW_COUNT - WIN_LENGTH + 1):
        for col in range(COLUMN_COUNT - WIN_LENGTH + 1):
            window = [(row + offset, col + offset) for offset in range(WIN_LENGTH)]
            if all(board[r][c] == player for r, c in window):
                return window

    # --- 4. DIAGONAL UP-RIGHT CHECK (↗) ---
    # Starting positions must leave enough room to the right AND up.
    # So the starting row must be at least WIN_LENGTH - 1.
    for row in range(WIN_LENGTH - 1, ROW_COUNT):
        for col in range(COLUMN_COUNT - WIN_LENGTH + 1):
            window = [(row - offset, col + offset) for offset in range(WIN_LENGTH)]
            if all(board[r][c] == player for r, c in window):
                return window

    # No winning line found anywhere on the board.
    return None


def is_board_full(board):
    """
    Return True if every cell on the board is filled.
    Used to detect a tie/draw when no one has won.
    """
    # If the TOP row has no empty cells, the whole board must be full
    # (because discs always stack from the bottom up).
    return all(cell != EMPTY for cell in board[0])


# =============================================================================
# DRAWING FUNCTIONS
# =============================================================================
# These functions draw the game to the screen. Pygame uses a "coordinate
# system" where (0, 0) is the TOP-LEFT corner of the window, X increases
# to the RIGHT, and Y increases DOWNWARD.
# =============================================================================

def draw_board(surface, board, winning_cells=None):
    """
    Draw the entire board: background, blue board, empty slots, and all discs.
    If winning_cells is provided (a list of (row, col) tuples), those discs
    get a highlight circle around them.
    """

    # Step 1: Fill the whole window with the background color.
    # This also clears anything drawn on the previous frame.
    surface.fill(BACKGROUND_COLOR)

    # Step 2: Draw the blue rectangular board. It starts below the preview
    # area (at y = PREVIEW_HEIGHT) and extends to the bottom of the window.
    board_rect = pygame.Rect(
        0,                              # x: left edge of window
        PREVIEW_HEIGHT,                 # y: just below the preview strip
        WINDOW_WIDTH,                   # width: full window width
        ROW_COUNT * SQUARE_SIZE         # height: as tall as the grid
    )
    pygame.draw.rect(surface, BOARD_COLOR, board_rect)

    # Step 3: For each cell, draw either an empty slot or a player's disc.
    for row in range(ROW_COUNT):
        for col in range(COLUMN_COUNT):
            # Calculate the CENTER point of this cell in pixel coordinates.
            # The "+ SQUARE_SIZE // 2" moves from the top-left corner
            # of the cell to its center.
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2 + PREVIEW_HEIGHT

            # Decide what color to draw based on what (if anything) is in this cell.
            cell_value = board[row][col]
            if cell_value == PLAYER_1:
                disc_color = PLAYER_1_COLOR
            elif cell_value == PLAYER_2:
                disc_color = PLAYER_2_COLOR
            else:
                disc_color = EMPTY_SLOT_COLOR  # Draw the "hole" in the board

            # Draw the circle. pygame.draw.circle takes:
            # (surface, color, center_point, radius)
            pygame.draw.circle(surface, disc_color, (center_x, center_y), DISC_RADIUS)

            # If this cell is part of the winning line, draw a highlight
            # ring around it. The '2' at the end is the ring's line width.
            if winning_cells and (row, col) in winning_cells:
                pygame.draw.circle(
                    surface,
                    WIN_HIGHLIGHT_COLOR,
                    (center_x, center_y),
                    DISC_RADIUS,
                    4  # line thickness — higher = thicker ring
                )


def draw_preview_disc(surface, mouse_x, current_player):
    """
    Draw the floating preview disc at the top of the screen that follows
    the mouse cursor. This shows the player where their disc will drop.
    """
    # Figure out which column the mouse is over.
    # Integer division (//) rounds down to give us a column index.
    column = mouse_x // SQUARE_SIZE

    # Clamp the column to valid range, just in case the mouse is slightly
    # off-screen (this can happen during window resizing, for example).
    if column < 0:
        column = 0
    elif column >= COLUMN_COUNT:
        column = COLUMN_COUNT - 1

    # Pick the color based on whose turn it is.
    disc_color = PLAYER_1_COLOR if current_player == PLAYER_1 else PLAYER_2_COLOR

    # Center the preview disc horizontally in its column, and vertically
    # within the preview strip at the top.
    center_x = column * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = PREVIEW_HEIGHT // 2

    pygame.draw.circle(surface, disc_color, (center_x, center_y), DISC_RADIUS)


def draw_message(surface, title_text, subtitle_text, title_font, info_font):
    """
    Draw a centered end-of-game message with a big title and a smaller
    subtitle underneath. Used for win and tie announcements.
    """
    # Render (draw) the title text into a new image ("surface").
    # render() arguments: (text, antialias=True for smooth edges, color)
    title_surface = title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surface = info_font.render(subtitle_text, True, TEXT_COLOR)

    # get_rect() returns a rectangle describing the text's size. We use
    # 'center=' to position it neatly in the middle of the window.
    title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
    subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))

    # Draw a semi-transparent dark overlay so the text stands out against
    # a potentially busy board behind it.
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))  # The 4th number (160) is alpha/transparency (0-255)
    surface.blit(overlay, (0, 0))  # blit() means "paste this image onto the surface"

    # Finally, paste the text onto the main surface at the rectangle's position.
    surface.blit(title_surface, title_rect)
    surface.blit(subtitle_surface, subtitle_rect)


# =============================================================================
# MAIN GAME FUNCTION
# =============================================================================
# This is the heart of the program — it sets things up and runs the
# "game loop" that keeps the game going frame by frame.
# =============================================================================

def main():
    """Run the Connect Four game."""

    # --- Initialize Pygame ---
    # This gets Pygame's internal systems (graphics, input, etc.) ready.
    # You must call this before using most Pygame features.
    pygame.init()

    # --- Create the game window ---
    # set_mode() creates the window and returns a "surface" we draw on.
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Connect Four")  # Text shown in the title bar

    # --- Create fonts for text rendering ---
    # None = use the default system font. Replace with a filename (like
    # "arial.ttf") if you want a specific font, but that requires the font
    # file to exist on the user's computer.
    title_font = pygame.font.SysFont(None, TITLE_FONT_SIZE)
    info_font = pygame.font.SysFont(None, INFO_FONT_SIZE)

    # --- Clock for controlling frame rate ---
    # This makes sure the game runs at a consistent speed regardless of
    # how fast the computer is.
    clock = pygame.time.Clock()

    # --- Set up the initial game state ---
    board = create_empty_board()
    current_player = PLAYER_1       # Red always goes first
    game_over = False               # True when someone wins or it's a tie
    winner = None                   # Will be set to PLAYER_1 or PLAYER_2 on a win
    winning_cells = None            # List of cells forming the winning line
    is_tie = False                  # True if the board filled up with no winner

    # =========================================================================
    # THE GAME LOOP
    # =========================================================================
    # Every game has a loop like this. On each iteration (each "frame"), we:
    #   1. Handle events (input like clicks, key presses, quitting).
    #   2. Update the game state if anything changed.
    #   3. Draw the current state to the screen.
    #   4. Wait briefly so we don't run too fast.
    # =========================================================================
    running = True
    while running:

        # Get the current mouse position — used to draw the preview disc.
        # This returns an (x, y) tuple in pixel coordinates.
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # --- 1. EVENT HANDLING ---
        # pygame.event.get() returns a list of everything that has happened
        # since the last frame: key presses, mouse clicks, window close, etc.
        for event in pygame.event.get():

            # The user clicked the window's close (X) button.
            if event.type == pygame.QUIT:
                running = False

            # The user pressed a keyboard key.
            elif event.type == pygame.KEYDOWN:
                # ESC quits the game.
                if event.key == pygame.K_ESCAPE:
                    running = False
                # R restarts the game (only meaningful if the game is over).
                elif event.key == pygame.K_r and game_over:
                    # Reset all game state back to the starting values.
                    board = create_empty_board()
                    current_player = PLAYER_1
                    game_over = False
                    winner = None
                    winning_cells = None
                    is_tie = False

            # The user clicked a mouse button.
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                # event.button == 1 means the LEFT mouse button.
                # We ignore middle (2) and right (3) clicks.
                if event.button == 1:
                    # Figure out which column was clicked.
                    column = mouse_x // SQUARE_SIZE

                    # Only proceed if the click is on a valid, non-full column.
                    if is_column_valid(board, column):
                        # Find where the disc will land and place it there.
                        row = get_next_open_row(board, column)
                        drop_disc(board, row, column, current_player)

                        # After the move, check for a win or tie.
                        winning_cells = check_for_win(board, current_player)
                        if winning_cells is not None:
                            winner = current_player
                            game_over = True
                        elif is_board_full(board):
                            is_tie = True
                            game_over = True
                        else:
                            # No win, no tie — switch to the other player.
                            # A compact way to "swap" between PLAYER_1 and PLAYER_2:
                            # if current == 1, next is 2; if current == 2, next is 1.
                            current_player = PLAYER_2 if current_player == PLAYER_1 else PLAYER_1

        # --- 2 & 3. DRAW THE SCREEN ---
        # Draw the board (and winning highlight if applicable).
        draw_board(screen, board, winning_cells)

        # If the game is still going, show the preview disc at the top.
        if not game_over:
            draw_preview_disc(screen, mouse_x, current_player)

        # If the game is over, overlay the end-of-game message.
        if game_over:
            if is_tie:
                title_text = "It's a Tie!"
            elif winner == PLAYER_1:
                title_text = "Player 1 (Red) Wins!"
            else:
                title_text = "Player 2 (Yellow) Wins!"
            subtitle_text = "Press R to restart or ESC to quit"
            draw_message(screen, title_text, subtitle_text, title_font, info_font)

        # Swap the newly-drawn frame onto the actual visible window.
        # (Pygame draws to an off-screen buffer first for smoothness.)
        pygame.display.flip()

        # --- 4. CONTROL FRAME RATE ---
        # Pause just enough so we run at FPS frames per second, no faster.
        clock.tick(FPS)

    # --- Clean up and exit ---
    # When the loop ends, close Pygame and quit the program gracefully.
    pygame.quit()
    sys.exit()


# =============================================================================
# PROGRAM ENTRY POINT
# =============================================================================
# This special check means: "only run main() if this file is being run
# directly by the user, not if it's being imported as a module."
# It's a standard Python convention — good habit to get used to!
# =============================================================================

if __name__ == "__main__":
    main()
