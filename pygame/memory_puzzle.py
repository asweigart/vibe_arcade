"""
Memory Puzzle Game
==================
A classic card-matching memory game built with Pygame.

How to play:
  - Click cards to flip them over.
  - Try to find matching pairs.
  - Match all pairs to win!
  - Press 'R' to restart at any time.

This file is heavily commented to help beginner programmers understand
each part of the code. Everything is in one file and uses only built-in
Python libraries plus Pygame - no external images or sounds needed.
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
# Pygame is the library that handles graphics, input, and the game window.
# 'random' is used to shuffle the cards so each game is different.
# 'sys' gives us access to sys.exit() for cleanly closing the program.
import pygame
import random
import sys

# -----------------------------------------------------------------------------
# CONSTANTS (configuration values that never change while the game runs)
# -----------------------------------------------------------------------------
# Using ALL_CAPS for constants is a Python convention. It makes them easy
# to spot and tells other programmers "don't change these at runtime."

# --- Grid settings ---
# The board will be BOARD_COLS wide and BOARD_ROWS tall.
# The total number of cards must be EVEN (because cards come in pairs).
BOARD_COLS = 6   # number of columns of cards
BOARD_ROWS = 4   # number of rows of cards
# Sanity check: 6 * 4 = 24 cards = 12 pairs. Good!

# --- Card dimensions (in pixels) ---
CARD_WIDTH = 80
CARD_HEIGHT = 80
CARD_GAP = 10    # space between cards

# --- Window dimensions ---
# We calculate the window size from the board size so the board is centered.
# The extra space on top (TOP_MARGIN) leaves room for the score/status text.
SIDE_MARGIN = 40
TOP_MARGIN = 80
WINDOW_WIDTH = BOARD_COLS * CARD_WIDTH + (BOARD_COLS - 1) * CARD_GAP + SIDE_MARGIN * 2
WINDOW_HEIGHT = BOARD_ROWS * CARD_HEIGHT + (BOARD_ROWS - 1) * CARD_GAP + TOP_MARGIN + SIDE_MARGIN

# --- Frames per second ---
# 60 FPS gives smooth animation without using too much CPU.
FPS = 60

# --- How long to show a non-matching pair before flipping them back (milliseconds) ---
MISMATCH_DELAY = 800

# --- Colors (Red, Green, Blue tuples; each value from 0 to 255) ---
BG_COLOR         = (30, 30, 46)    # dark blue-gray background
CARD_BACK_COLOR  = (88, 91, 112)   # gray for face-down cards
CARD_BACK_ACCENT = (69, 71, 90)    # slightly darker for the card back pattern
MATCHED_COLOR    = (80, 100, 80)   # dimmer tone for matched (solved) cards
TEXT_COLOR       = (205, 214, 244) # off-white for text
HIGHLIGHT_COLOR  = (249, 226, 175) # yellow for highlighting the hovered card

# --- Palette of bright colors for the card "faces" ---
# Each pair of cards will get a unique (color, shape) combination.
# We use color + shape so pairs are easy to tell apart visually.
CARD_COLORS = [
    (243, 139, 168),  # pink
    (250, 179, 135),  # peach
    (249, 226, 175),  # yellow
    (166, 227, 161),  # green
    (148, 226, 213),  # teal
    (137, 180, 250),  # blue
    (203, 166, 247),  # mauve
    (245, 194, 231),  # lavender-pink
    (180, 190, 254),  # periwinkle
    (116, 199, 236),  # sky blue
    (210, 215, 236),  # light gray
    (242, 205, 205),  # rosewater
]

# --- Shapes we can draw on cards. These are just string identifiers ---
# we'll check in the draw function to decide what to render.
CARD_SHAPES = ['circle', 'square', 'triangle', 'diamond',
               'star', 'heart', 'cross', 'hexagon']


# -----------------------------------------------------------------------------
# HELPER: GENERATE THE BOARD
# -----------------------------------------------------------------------------
def create_board():
    """
    Build a randomized 2D list representing the board.

    Each cell on the board is a dictionary with three pieces of info:
      - 'icon':     a (color, shape) tuple. Matching cards share the same icon.
      - 'revealed': True if the card is currently flipped face-up.
      - 'matched':  True if the card has already been matched (solved).

    Returns the 2D list (a list of rows, where each row is a list of cells).
    """
    # Figure out how many unique card faces (icons) we need.
    # Total cards / 2 gives us the number of pairs needed.
    total_cards = BOARD_COLS * BOARD_ROWS
    num_pairs = total_cards // 2

    # Build every possible (color, shape) combination.
    # Then shuffle and pick just enough unique icons for our pairs.
    all_icons = [(color, shape) for color in CARD_COLORS for shape in CARD_SHAPES]
    random.shuffle(all_icons)
    chosen_icons = all_icons[:num_pairs]

    # Duplicate each icon so every icon appears exactly twice (to make pairs).
    # Then shuffle so the positions of matching cards are random.
    icons = chosen_icons * 2
    random.shuffle(icons)

    # Convert the flat list of icons into a 2D grid.
    # We use nested loops: outer loop = rows, inner loop = columns.
    board = []
    for row in range(BOARD_ROWS):
        board_row = []  # one row of cards
        for col in range(BOARD_COLS):
            # Pop the next icon off the list and wrap it in a card dictionary.
            icon = icons.pop()
            card = {'icon': icon, 'revealed': False, 'matched': False}
            board_row.append(card)
        board.append(board_row)

    return board


# -----------------------------------------------------------------------------
# HELPER: CONVERT BETWEEN BOARD COORDS AND SCREEN PIXELS
# -----------------------------------------------------------------------------
def card_top_left(col, row):
    """
    Given a column and row index, return the (x, y) pixel position of the
    top-left corner of that card on the screen.
    """
    x = SIDE_MARGIN + col * (CARD_WIDTH + CARD_GAP)
    y = TOP_MARGIN + row * (CARD_HEIGHT + CARD_GAP)
    return x, y


def pixel_to_card(pos):
    """
    Given a (x, y) pixel position (for example, a mouse click),
    return the (col, row) of the card that was clicked, or None if the
    click didn't land on any card.
    """
    mouse_x, mouse_y = pos
    # Check every card. We could compute the col/row mathematically, but a
    # loop is simpler and easier to understand for beginners.
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            x, y = card_top_left(col, row)
            # A pygame.Rect makes it easy to test if a point is inside a box.
            rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
            if rect.collidepoint(mouse_x, mouse_y):
                return col, row
    # If we fell out of the loop, the click missed every card.
    return None


# -----------------------------------------------------------------------------
# DRAWING: CARD SHAPES
# -----------------------------------------------------------------------------
def draw_shape(surface, shape, color, rect):
    """
    Draw a specific shape inside the given rect (card area) on the surface.

    Parameters:
      surface : the pygame surface (usually the window) to draw onto
      shape   : a string like 'circle', 'triangle', etc.
      color   : the (R, G, B) color to draw the shape with
      rect    : a pygame.Rect that defines the card's position and size
    """
    # Figure out the center of the card and a "radius" we'll base shapes on.
    cx = rect.centerx
    cy = rect.centery
    # Padding keeps the shape from touching the card edges.
    padding = 14
    size = min(rect.width, rect.height) - padding * 2
    half = size // 2

    if shape == 'circle':
        pygame.draw.circle(surface, color, (cx, cy), half)

    elif shape == 'square':
        # inflate(-x, -y) shrinks the rect to add padding on all sides.
        pygame.draw.rect(surface, color, rect.inflate(-padding * 2, -padding * 2))

    elif shape == 'triangle':
        # A triangle needs three points. We build it pointing upward.
        points = [
            (cx, cy - half),              # top
            (cx - half, cy + half),       # bottom left
            (cx + half, cy + half),       # bottom right
        ]
        pygame.draw.polygon(surface, color, points)

    elif shape == 'diamond':
        # A diamond is a square rotated 45 degrees - four points on the axes.
        points = [
            (cx, cy - half),   # top
            (cx + half, cy),   # right
            (cx, cy + half),   # bottom
            (cx - half, cy),   # left
        ]
        pygame.draw.polygon(surface, color, points)

    elif shape == 'star':
        # A 5-pointed star has 10 points total (alternating outer/inner).
        # We'll use some basic math (sin/cos) to find each point.
        import math
        points = []
        outer_r = half
        inner_r = half // 2
        # Start the first point at the top (angle = -90 degrees).
        for i in range(10):
            angle_deg = -90 + i * 36           # 360 / 10 = 36 degrees per point
            angle_rad = math.radians(angle_deg)
            r = outer_r if i % 2 == 0 else inner_r
            px = cx + r * math.cos(angle_rad)
            py = cy + r * math.sin(angle_rad)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)

    elif shape == 'heart':
        # Approximate a heart: two circles for the lobes + a triangle for the point.
        lobe_r = half // 2
        # Left lobe
        pygame.draw.circle(surface, color, (cx - lobe_r // 1, cy - lobe_r // 2), lobe_r)
        # Right lobe
        pygame.draw.circle(surface, color, (cx + lobe_r // 1, cy - lobe_r // 2), lobe_r)
        # Bottom triangle
        points = [
            (cx - half, cy - lobe_r // 4),
            (cx + half, cy - lobe_r // 4),
            (cx, cy + half),
        ]
        pygame.draw.polygon(surface, color, points)

    elif shape == 'cross':
        # A plus-shape made from two overlapping rectangles.
        thickness = size // 3
        # Horizontal bar
        h_rect = pygame.Rect(0, 0, size, thickness)
        h_rect.center = (cx, cy)
        pygame.draw.rect(surface, color, h_rect)
        # Vertical bar
        v_rect = pygame.Rect(0, 0, thickness, size)
        v_rect.center = (cx, cy)
        pygame.draw.rect(surface, color, v_rect)

    elif shape == 'hexagon':
        # A hexagon has 6 points spaced 60 degrees apart.
        import math
        points = []
        for i in range(6):
            angle_deg = -90 + i * 60
            angle_rad = math.radians(angle_deg)
            px = cx + half * math.cos(angle_rad)
            py = cy + half * math.sin(angle_rad)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)


# -----------------------------------------------------------------------------
# DRAWING: THE WHOLE BOARD
# -----------------------------------------------------------------------------
def draw_board(surface, board, hover_cell):
    """
    Draw every card on the screen.

    Parameters:
      surface    : the window surface to draw on
      board      : the 2D list of cards from create_board()
      hover_cell : the (col, row) the mouse is currently over, or None
    """
    # Fill the whole window with the background color before drawing anything.
    surface.fill(BG_COLOR)

    # Loop through every card position on the board.
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            card = board[row][col]
            x, y = card_top_left(col, row)
            rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

            if card['matched']:
                # Matched cards are drawn in a muted style so the player
                # can see progress at a glance but they no longer stand out.
                pygame.draw.rect(surface, MATCHED_COLOR, rect, border_radius=8)
                color, shape = card['icon']
                # Dim the color so it looks "solved" rather than active.
                dim_color = tuple(c // 2 for c in color)
                draw_shape(surface, shape, dim_color, rect)

            elif card['revealed']:
                # Face-up card: draw a white-ish background and the icon on top.
                pygame.draw.rect(surface, (230, 230, 240), rect, border_radius=8)
                color, shape = card['icon']
                draw_shape(surface, shape, color, rect)

            else:
                # Face-down card: draw the card back.
                pygame.draw.rect(surface, CARD_BACK_COLOR, rect, border_radius=8)
                # A little pattern (a smaller diamond) so the back isn't bland.
                inner = rect.inflate(-30, -30)
                points = [
                    (inner.centerx, inner.top),
                    (inner.right, inner.centery),
                    (inner.centerx, inner.bottom),
                    (inner.left, inner.centery),
                ]
                pygame.draw.polygon(surface, CARD_BACK_ACCENT, points)

            # Highlight the card under the mouse (only if it's still playable).
            if hover_cell == (col, row) and not card['matched'] and not card['revealed']:
                pygame.draw.rect(surface, HIGHLIGHT_COLOR, rect, width=3, border_radius=8)


# -----------------------------------------------------------------------------
# DRAWING: THE TOP STATUS BAR (moves, matches, win message)
# -----------------------------------------------------------------------------
def draw_status(surface, font, big_font, moves, matches_found, total_pairs, won):
    """
    Draw the status text at the top of the window.
    """
    if won:
        # Big celebratory message when the player finds every pair.
        text = f"You won in {moves} moves! Press R to play again."
        rendered = big_font.render(text, True, HIGHLIGHT_COLOR)
    else:
        # Normal status: show how many pairs they've found and total moves.
        text = f"Matches: {matches_found}/{total_pairs}    Moves: {moves}    (R to restart)"
        rendered = font.render(text, True, TEXT_COLOR)

    # Center the text horizontally at the top of the window.
    rect = rendered.get_rect(center=(WINDOW_WIDTH // 2, TOP_MARGIN // 2))
    surface.blit(rendered, rect)


# -----------------------------------------------------------------------------
# MAIN GAME LOOP
# -----------------------------------------------------------------------------
def main():
    """
    The main function: initialize Pygame, create the window, and run the
    game loop that handles events, updates state, and redraws the screen.
    """
    # pygame.init() starts up all pygame modules (graphics, fonts, etc.)
    pygame.init()

    # Create the game window and give it a title.
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Memory Puzzle")

    # Clock is used to cap the frame rate so the game runs at a steady speed.
    clock = pygame.time.Clock()

    # Create two fonts: a regular one for the status bar, a big one for "You won!"
    # Passing None to SysFont uses pygame's default font, which always works.
    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 36)

    # --- Game state variables ---
    # These change over time as the player plays.
    board = create_board()             # the 2D list of cards
    first_selection = None             # (col, row) of the first flipped card, or None
    second_selection = None            # (col, row) of the second flipped card, or None
    mismatch_time = 0                  # pygame tick when a mismatched pair was shown
    moves = 0                          # how many pairs the player has tried
    matches_found = 0                  # pairs successfully matched
    total_pairs = (BOARD_COLS * BOARD_ROWS) // 2
    won = False                        # becomes True when all pairs are matched

    # -------------------------------------------------------------------------
    # The main loop runs once per frame. It does three things:
    #   1. Handle events (clicks, key presses, closing the window)
    #   2. Update the game state (flip cards, check for matches, etc.)
    #   3. Draw the current state to the screen
    # -------------------------------------------------------------------------
    running = True
    while running:
        # Current time in milliseconds since pygame started. Used for timing
        # how long to show a mismatched pair before flipping them back.
        now = pygame.time.get_ticks()

        # Where is the mouse right now? Used to highlight the hovered card.
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = pixel_to_card(mouse_pos)

        # --- 1. HANDLE EVENTS -------------------------------------------------
        # pygame.event.get() returns a list of everything the user did since
        # the last frame (clicks, keys pressed, window closed, etc.)
        for event in pygame.event.get():

            # User clicked the window's close button.
            if event.type == pygame.QUIT:
                running = False

            # User pressed a key.
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # 'R' restarts the game by rebuilding the board and
                    # resetting the game-state variables.
                    board = create_board()
                    first_selection = None
                    second_selection = None
                    mismatch_time = 0
                    moves = 0
                    matches_found = 0
                    won = False
                elif event.key == pygame.K_ESCAPE:
                    # Also allow ESC to quit - a nice convenience.
                    running = False

            # User clicked the mouse.
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Ignore clicks while we're showing a mismatched pair
                # (otherwise the player could cheat and flip extra cards).
                if second_selection is not None:
                    continue
                # Ignore clicks after winning - nothing to do.
                if won:
                    continue

                clicked = pixel_to_card(event.pos)
                if clicked is None:
                    # The player clicked outside any card. Nothing to do.
                    continue

                col, row = clicked
                card = board[row][col]

                # Can't click a card that's already matched or already face-up.
                if card['matched'] or card['revealed']:
                    continue

                # Flip the card face-up.
                card['revealed'] = True

                if first_selection is None:
                    # This was the first card of a pair attempt.
                    first_selection = (col, row)
                else:
                    # This is the second card. Now we have a complete attempt.
                    second_selection = (col, row)
                    moves += 1

                    # Compare the two cards' icons.
                    c1, r1 = first_selection
                    c2, r2 = second_selection
                    if board[r1][c1]['icon'] == board[r2][c2]['icon']:
                        # Match! Mark them as solved and clear the selections
                        # immediately so the player can keep playing.
                        board[r1][c1]['matched'] = True
                        board[r2][c2]['matched'] = True
                        matches_found += 1
                        first_selection = None
                        second_selection = None
                        # Did that match complete the game?
                        if matches_found == total_pairs:
                            won = True
                    else:
                        # Not a match. Record the time so we can flip them
                        # back after a short delay (handled below).
                        mismatch_time = now

        # --- 2. UPDATE STATE --------------------------------------------------
        # If we're currently showing a mismatched pair and enough time has
        # passed, flip both cards back face-down and clear the selections.
        if second_selection is not None and (now - mismatch_time) >= MISMATCH_DELAY:
            c1, r1 = first_selection
            c2, r2 = second_selection
            # Only hide them if they weren't matched (sanity check - by this
            # point we know they weren't, but defensive coding is good).
            if not board[r1][c1]['matched']:
                board[r1][c1]['revealed'] = False
            if not board[r2][c2]['matched']:
                board[r2][c2]['revealed'] = False
            first_selection = None
            second_selection = None

        # --- 3. DRAW ---------------------------------------------------------
        # Redraw the entire screen from scratch every frame. It's simple and
        # plenty fast for a game with this few moving parts.
        draw_board(screen, board, hover_cell)
        draw_status(screen, font, big_font, moves, matches_found, total_pairs, won)

        # pygame uses a "double buffer" - we draw off-screen, then flip() shows
        # the finished frame all at once. This avoids flicker.
        pygame.display.flip()

        # Wait just long enough to maintain FPS frames per second.
        clock.tick(FPS)

    # --- CLEAN UP ------------------------------------------------------------
    # When the loop ends (user closed the window), shut down pygame and exit.
    pygame.quit()
    sys.exit()


# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
# This check ensures main() only runs when we execute this file directly
# (not if some other script imports it). It's a standard Python idiom.
if __name__ == '__main__':
    main()
