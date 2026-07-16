"""
TETRIS - A classic falling-block puzzle game
=============================================
Built with Python's built-in 'turtle' module for graphics.

HOW TO PLAY:
  Left Arrow / A  = Move piece left
  Right Arrow / D = Move piece right
  Up Arrow / W    = Rotate piece
  Down Arrow / S  = Soft drop (move piece down faster)
  Space           = Hard drop (instantly drop piece to bottom)
  Escape / P      = Pause / Unpause (board is hidden while paused)

GOAL:
  Fill complete horizontal rows to clear them and earn points.
  The game ends when new pieces can no longer fit on the board.

SCORING:
  1 line  = 100 points
  2 lines = 300 points
  3 lines = 500 points
  4 lines = 800 points (called a "Tetris!")
"""

import turtle
import random

# =============================================================================
# GAME CONSTANTS - Easy to tweak these to change the game's look and feel
# =============================================================================

# Board dimensions (in number of cells)
BOARD_WIDTH = 10    # Standard Tetris is 10 columns wide
BOARD_HEIGHT = 20   # Standard Tetris is 20 rows tall

# Size of each square cell in pixels
CELL_SIZE = 30

# How often the piece falls down one row (in milliseconds)
# Lower number = faster game. We'll speed up as the level increases.
INITIAL_FALL_SPEED = 500

# Colors for the background and grid
BACKGROUND_COLOR = "#1a1a2e"
GRID_COLOR = "#2a2a4a"
BORDER_COLOR = "#e94560"
TEXT_COLOR = "#eaeaea"
GHOST_COLOR = "#444466"

# Calculate pixel positions for the board
# The board is centered horizontally, with some extra space on the right for score
BOARD_PIXEL_WIDTH = BOARD_WIDTH * CELL_SIZE
BOARD_PIXEL_HEIGHT = BOARD_HEIGHT * CELL_SIZE

# Top-left corner of the board in turtle coordinates
# Turtle's (0,0) is in the center of the screen, so we offset accordingly
BOARD_LEFT = -(BOARD_PIXEL_WIDTH // 2) - 80
BOARD_TOP = BOARD_PIXEL_HEIGHT // 2

# Where to display the score and next piece (to the right of the board)
INFO_X = BOARD_LEFT + BOARD_PIXEL_WIDTH + 40

# =============================================================================
# TETROMINO DEFINITIONS
# =============================================================================
# Each tetromino (piece) is defined as a list of (row, col) offsets.
# The offsets describe where each block sits relative to a reference point.
# Each piece also has an assigned color.
#
# The 7 standard Tetris pieces are:
#   I, O, T, S, Z, L, J
# =============================================================================

TETROMINOES = {
    "I": {
        "shape": [(0, 0), (0, 1), (0, 2), (0, 3)],
        "color": "#00d2ff",  # Cyan
    },
    "O": {
        "shape": [(0, 0), (0, 1), (1, 0), (1, 1)],
        "color": "#ffd700",  # Yellow
    },
    "T": {
        "shape": [(0, 0), (0, 1), (0, 2), (1, 1)],
        "color": "#b24eff",  # Purple
    },
    "S": {
        "shape": [(0, 1), (0, 2), (1, 0), (1, 1)],
        "color": "#00ff88",  # Green
    },
    "Z": {
        "shape": [(0, 0), (0, 1), (1, 1), (1, 2)],
        "color": "#ff4444",  # Red
    },
    "L": {
        "shape": [(0, 0), (0, 1), (0, 2), (1, 0)],
        "color": "#ff8c00",  # Orange
    },
    "J": {
        "shape": [(0, 0), (0, 1), (0, 2), (1, 2)],
        "color": "#4488ff",  # Blue
    },
}

# =============================================================================
# GAME STATE
# =============================================================================
# We use a simple dictionary to hold all the game state in one place.
# This makes it easy to see what data the game tracks.
# =============================================================================

game = {
    # The board is a 2D grid. Each cell is either None (empty) or a color string.
    # board[row][col] — row 0 is the TOP of the board.
    "board": [],

    # The currently falling piece
    "current_piece": None,       # List of (row, col) positions on the board
    "current_color": None,       # Color string for the current piece
    "current_type": None,        # Letter name like "T", "I", etc.

    # The next piece (shown in the preview box)
    "next_type": None,

    # Position of the piece's reference point on the board
    "piece_row": 0,
    "piece_col": 0,

    # The shape offsets for the current rotation
    "current_offsets": [],

    # Score and level tracking
    "score": 0,
    "level": 1,
    "lines_cleared": 0,

    # Game flow control
    "game_over": False,
    "paused": False,
    "fall_speed": INITIAL_FALL_SPEED,
}


# =============================================================================
# BOARD FUNCTIONS
# =============================================================================

def create_empty_board():
    """
    Create a fresh empty board — a 2D list filled with None values.
    None means the cell is empty; a color string means it's occupied.
    """
    board = []
    for row in range(BOARD_HEIGHT):
        # Each row is a list of BOARD_WIDTH cells, all starting as None
        new_row = []
        for col in range(BOARD_WIDTH):
            new_row.append(None)
        board.append(new_row)
    return board


def is_cell_on_board(row, col):
    """Check if a (row, col) position is within the board boundaries."""
    if row < 0 or row >= BOARD_HEIGHT:
        return False
    if col < 0 or col >= BOARD_WIDTH:
        return False
    return True


def is_cell_empty(board, row, col):
    """Check if a specific cell on the board is empty (not occupied by a locked piece)."""
    if not is_cell_on_board(row, col):
        return False
    return board[row][col] is None


# =============================================================================
# PIECE FUNCTIONS
# =============================================================================

def get_piece_cells(offsets, anchor_row, anchor_col):
    """
    Given a list of (row_offset, col_offset) pairs and an anchor position,
    calculate the actual board positions for each block of the piece.

    For example, if the anchor is at row=2, col=3 and one offset is (0, 1),
    that block would be at board position (2, 4).
    """
    cells = []
    for row_offset, col_offset in offsets:
        actual_row = anchor_row + row_offset
        actual_col = anchor_col + col_offset
        cells.append((actual_row, actual_col))
    return cells


def can_piece_fit(board, offsets, anchor_row, anchor_col):
    """
    Check if a piece (defined by its offsets and anchor position)
    can fit on the board without overlapping locked blocks or going out of bounds.
    """
    cells = get_piece_cells(offsets, anchor_row, anchor_col)
    for row, col in cells:
        # Check if the cell is outside the board
        if not is_cell_on_board(row, col):
            return False
        # Check if the cell is already occupied by a locked piece
        if board[row][col] is not None:
            return False
    return True


def rotate_offsets_clockwise(offsets):
    """
    Rotate piece offsets 90 degrees clockwise.

    The math for a clockwise rotation is:
        new_row = old_col
        new_col = -old_row

    After rotating, we shift everything so the minimum row and col are 0.
    This keeps the piece near its anchor point.
    """
    rotated = []
    for row, col in offsets:
        new_row = col
        new_col = -row
        rotated.append((new_row, new_col))

    # Find the minimum row and column so we can shift to (0, 0) origin
    min_row = min(r for r, c in rotated)
    min_col = min(c for r, c in rotated)

    # Shift all offsets so the top-left is at (0, 0)
    normalized = []
    for row, col in rotated:
        normalized.append((row - min_row, col - min_col))

    return normalized


def spawn_piece(game_state):
    """
    Place a new piece at the top of the board.
    If the piece can't fit, the game is over.
    """
    # Use the "next" piece, then pick a new "next"
    piece_type = game_state["next_type"]
    game_state["next_type"] = random.choice(list(TETROMINOES.keys()))

    piece_data = TETROMINOES[piece_type]
    offsets = list(piece_data["shape"])  # Make a copy so we don't modify the original
    color = piece_data["color"]

    # Start the piece at the top center of the board
    start_row = 0
    start_col = BOARD_WIDTH // 2 - 1  # Roughly centered

    # Check if the piece can fit at the starting position
    if not can_piece_fit(game_state["board"], offsets, start_row, start_col):
        game_state["game_over"] = True
        return

    # Store the piece info in the game state
    game_state["current_offsets"] = offsets
    game_state["current_color"] = color
    game_state["current_type"] = piece_type
    game_state["piece_row"] = start_row
    game_state["piece_col"] = start_col
    game_state["current_piece"] = get_piece_cells(offsets, start_row, start_col)


def lock_piece(game_state):
    """
    Lock the current piece into the board.
    This happens when the piece can no longer move down.
    Each cell of the piece gets its color written into the board grid.
    """
    for row, col in game_state["current_piece"]:
        if is_cell_on_board(row, col):
            game_state["board"][row][col] = game_state["current_color"]


def get_ghost_position(game_state):
    """
    Calculate where the piece would land if it were dropped straight down.
    This is the "ghost" piece — a helpful preview shown at the bottom.
    """
    offsets = game_state["current_offsets"]
    ghost_row = game_state["piece_row"]
    ghost_col = game_state["piece_col"]

    # Move down one row at a time until the piece can't go further
    while can_piece_fit(game_state["board"], offsets, ghost_row + 1, ghost_col):
        ghost_row += 1

    return get_piece_cells(offsets, ghost_row, ghost_col)


# =============================================================================
# LINE CLEARING
# =============================================================================

def clear_full_lines(game_state):
    """
    Check every row of the board. If a row is completely filled (no empty cells),
    remove it and add a new empty row at the top.
    Returns the number of lines cleared.
    """
    board = game_state["board"]
    lines_cleared = 0

    # We check from bottom to top
    row = BOARD_HEIGHT - 1
    while row >= 0:
        # Check if every cell in this row is filled
        row_is_full = True
        for col in range(BOARD_WIDTH):
            if board[row][col] is None:
                row_is_full = False
                break

        if row_is_full:
            # Remove this row from the board
            board.pop(row)
            # Add a new empty row at the top
            empty_row = []
            for col in range(BOARD_WIDTH):
                empty_row.append(None)
            board.insert(0, empty_row)
            lines_cleared += 1
            # Don't move row index up — the rows above have shifted down,
            # so we need to check this same index again
        else:
            row -= 1

    return lines_cleared


def update_score(game_state, lines_cleared):
    """
    Award points based on how many lines were cleared at once.
    More lines at once = disproportionately more points (rewards skill!).
    """
    points_table = {
        1: 100,
        2: 300,
        3: 500,
        4: 800,  # The legendary "Tetris" — clearing 4 lines at once
    }

    if lines_cleared > 0:
        points = points_table.get(lines_cleared, 800)
        game_state["score"] += points * game_state["level"]
        game_state["lines_cleared"] += lines_cleared

        # Level up every 10 lines
        new_level = game_state["lines_cleared"] // 10 + 1
        if new_level > game_state["level"]:
            game_state["level"] = new_level
            # Make the game faster with each level (but not TOO fast)
            game_state["fall_speed"] = max(100, INITIAL_FALL_SPEED - (new_level - 1) * 40)


# =============================================================================
# MOVEMENT AND INPUT HANDLING
# =============================================================================

def move_piece(game_state, row_delta, col_delta):
    """
    Try to move the current piece by (row_delta, col_delta).
    Returns True if the move was successful, False if blocked.
    """
    new_row = game_state["piece_row"] + row_delta
    new_col = game_state["piece_col"] + col_delta

    if can_piece_fit(game_state["board"], game_state["current_offsets"], new_row, new_col):
        game_state["piece_row"] = new_row
        game_state["piece_col"] = new_col
        game_state["current_piece"] = get_piece_cells(
            game_state["current_offsets"], new_row, new_col
        )
        return True
    return False


def rotate_piece(game_state):
    """
    Try to rotate the current piece 90 degrees clockwise.
    If the rotated piece doesn't fit, try nudging it left or right ("wall kick").
    The O-piece (square) doesn't need rotation.
    """
    # The O-piece is a square — rotating it does nothing
    if game_state["current_type"] == "O":
        return

    new_offsets = rotate_offsets_clockwise(game_state["current_offsets"])

    # Try the rotation at the current position first
    if can_piece_fit(game_state["board"], new_offsets, game_state["piece_row"], game_state["piece_col"]):
        game_state["current_offsets"] = new_offsets
        game_state["current_piece"] = get_piece_cells(
            new_offsets, game_state["piece_row"], game_state["piece_col"]
        )
        return

    # "Wall kick" — try shifting left or right by 1 or 2 to make it fit
    for nudge in [1, -1, 2, -2]:
        test_col = game_state["piece_col"] + nudge
        if can_piece_fit(game_state["board"], new_offsets, game_state["piece_row"], test_col):
            game_state["current_offsets"] = new_offsets
            game_state["piece_col"] = test_col
            game_state["current_piece"] = get_piece_cells(
                new_offsets, game_state["piece_row"], test_col
            )
            return


def hard_drop(game_state):
    """
    Instantly drop the piece to the lowest possible position and lock it.
    """
    while move_piece(game_state, 1, 0):
        pass  # Keep moving down until we can't


# =============================================================================
# DRAWING FUNCTIONS
# =============================================================================

def cell_to_pixels(row, col):
    """
    Convert a board cell position (row, col) to turtle pixel coordinates (x, y).
    Turtle uses (x, y) where y increases upward, but our rows increase downward,
    so we flip the y direction.
    """
    x = BOARD_LEFT + col * CELL_SIZE
    y = BOARD_TOP - row * CELL_SIZE
    return x, y


def draw_filled_rect(drawer, x, y, width, height, fill_color, outline_color=None):
    """
    Draw a filled rectangle starting from its top-left corner at (x, y).
    The 'drawer' is a turtle object we use for drawing.
    """
    drawer.penup()
    drawer.goto(x, y)
    drawer.pendown()

    drawer.fillcolor(fill_color)
    if outline_color:
        drawer.pencolor(outline_color)
    else:
        drawer.pencolor(fill_color)

    drawer.begin_fill()
    # Draw four sides of the rectangle
    for side_length in [width, -height, -width, height]:
        if abs(side_length) == abs(width):
            drawer.forward(side_length) if side_length > 0 else drawer.forward(side_length)
        # We need to handle the direction properly
    # Actually, let's use a simpler approach — just trace the rectangle
    drawer.end_fill()

    # Simpler rectangle drawing with explicit corners
    drawer.penup()
    drawer.goto(x, y)
    drawer.pendown()
    drawer.fillcolor(fill_color)
    if outline_color:
        drawer.pencolor(outline_color)
        drawer.pensize(1)
    else:
        drawer.pencolor(fill_color)

    drawer.begin_fill()
    drawer.goto(x + width, y)           # Top-right
    drawer.goto(x + width, y - height)  # Bottom-right
    drawer.goto(x, y - height)          # Bottom-left
    drawer.goto(x, y)                   # Back to top-left
    drawer.end_fill()


def draw_block(drawer, row, col, color, outline="#111122"):
    """
    Draw a single Tetris block (one cell) at the given board position.
    Adds a slight 3D/beveled look with a lighter inner rectangle.
    """
    x, y = cell_to_pixels(row, col)
    padding = 1  # Small gap between blocks for a grid effect

    # Draw the main colored square
    draw_filled_rect(
        drawer,
        x + padding, y - padding,
        CELL_SIZE - 2 * padding, CELL_SIZE - 2 * padding,
        color, outline
    )

    # Draw a smaller, lighter rectangle inside for a shiny/beveled look
    highlight_size = CELL_SIZE * 0.3
    # We'll make the highlight color by appending transparency hint
    # Since turtle doesn't support alpha, we just use a lighter shade
    drawer.penup()
    drawer.goto(x + 3, y - 3)
    drawer.pendown()
    drawer.pencolor(color)
    drawer.pensize(1)
    # Draw a small L-shaped highlight on top and left edges
    drawer.goto(x + CELL_SIZE - 3, y - 3)


def draw_ghost_block(drawer, row, col):
    """
    Draw a ghost/shadow block — just an outline showing where the piece will land.
    """
    x, y = cell_to_pixels(row, col)
    padding = 2

    drawer.penup()
    drawer.goto(x + padding, y - padding)
    drawer.pendown()
    drawer.pencolor(GHOST_COLOR)
    drawer.pensize(2)
    # Draw just the outline (no fill)
    drawer.goto(x + CELL_SIZE - padding, y - padding)
    drawer.goto(x + CELL_SIZE - padding, y - CELL_SIZE + padding)
    drawer.goto(x + padding, y - CELL_SIZE + padding)
    drawer.goto(x + padding, y - padding)


def draw_board_border(drawer):
    """Draw a border around the game board."""
    x = BOARD_LEFT - 2
    y = BOARD_TOP + 2
    width = BOARD_PIXEL_WIDTH + 4
    height = BOARD_PIXEL_HEIGHT + 4

    drawer.penup()
    drawer.goto(x, y)
    drawer.pendown()
    drawer.pencolor(BORDER_COLOR)
    drawer.pensize(3)
    drawer.goto(x + width, y)
    drawer.goto(x + width, y - height)
    drawer.goto(x, y - height)
    drawer.goto(x, y)


def draw_grid_lines(drawer):
    """Draw subtle grid lines on the board so you can see the cells."""
    drawer.pencolor(GRID_COLOR)
    drawer.pensize(1)

    # Vertical lines
    for col in range(BOARD_WIDTH + 1):
        x = BOARD_LEFT + col * CELL_SIZE
        drawer.penup()
        drawer.goto(x, BOARD_TOP)
        drawer.pendown()
        drawer.goto(x, BOARD_TOP - BOARD_PIXEL_HEIGHT)

    # Horizontal lines
    for row in range(BOARD_HEIGHT + 1):
        y = BOARD_TOP - row * CELL_SIZE
        drawer.penup()
        drawer.goto(BOARD_LEFT, y)
        drawer.pendown()
        drawer.goto(BOARD_LEFT + BOARD_PIXEL_WIDTH, y)


def draw_next_piece_preview(drawer, piece_type):
    """
    Draw a small preview of the next piece in the info area on the right.
    """
    if piece_type is None:
        return

    piece_data = TETROMINOES[piece_type]
    offsets = piece_data["shape"]
    color = piece_data["color"]

    # Position for the preview box
    preview_x = INFO_X
    preview_y = BOARD_TOP - 80

    # Draw "NEXT" label
    drawer.penup()
    drawer.goto(preview_x + 10, preview_y + 30)
    drawer.pencolor(TEXT_COLOR)
    drawer.write("NEXT", font=("Courier", 14, "bold"))

    # Draw each block of the next piece
    preview_cell = 22  # Slightly smaller cells for the preview
    for row_off, col_off in offsets:
        bx = preview_x + col_off * preview_cell + 5
        by = preview_y - row_off * preview_cell
        draw_filled_rect(drawer, bx, by, preview_cell - 2, preview_cell - 2, color, "#111122")


def draw_score_info(drawer, game_state):
    """Display the score, level, and lines cleared on the right side."""
    drawer.penup()
    drawer.pencolor(TEXT_COLOR)

    # Score
    drawer.goto(INFO_X + 10, BOARD_TOP - 180)
    drawer.write("SCORE", font=("Courier", 14, "bold"))
    drawer.goto(INFO_X + 10, BOARD_TOP - 205)
    drawer.write(str(game_state["score"]), font=("Courier", 16, "normal"))

    # Level
    drawer.goto(INFO_X + 10, BOARD_TOP - 250)
    drawer.write("LEVEL", font=("Courier", 14, "bold"))
    drawer.goto(INFO_X + 10, BOARD_TOP - 275)
    drawer.write(str(game_state["level"]), font=("Courier", 16, "normal"))

    # Lines
    drawer.goto(INFO_X + 10, BOARD_TOP - 320)
    drawer.write("LINES", font=("Courier", 14, "bold"))
    drawer.goto(INFO_X + 10, BOARD_TOP - 345)
    drawer.write(str(game_state["lines_cleared"]), font=("Courier", 16, "normal"))


def draw_controls_help(drawer):
    """Show control instructions below the board."""
    drawer.penup()
    drawer.pencolor("#888899")
    help_x = INFO_X + 10
    help_y = BOARD_TOP - 420

    controls = [
        "CONTROLS:",
        "← → / A D  Move",
        "↑ / W      Rotate",
        "↓ / S      Soft drop",
        "Space       Hard drop",
        "Esc / P     Pause",
    ]
    for i, line in enumerate(controls):
        drawer.goto(help_x, help_y - i * 20)
        font_style = "bold" if i == 0 else "normal"
        drawer.write(line, font=("Courier", 10, font_style))


def draw_game_over(drawer):
    """Display a game over message in the center of the board."""
    center_x = BOARD_LEFT + BOARD_PIXEL_WIDTH // 2
    center_y = 30

    # Dark overlay box
    draw_filled_rect(
        drawer,
        BOARD_LEFT + 10, center_y + 50,
        BOARD_PIXEL_WIDTH - 20, 80,
        "#000000", BORDER_COLOR
    )

    drawer.penup()
    drawer.goto(center_x, center_y + 10)
    drawer.pencolor(BORDER_COLOR)
    drawer.write("GAME OVER", align="center", font=("Courier", 22, "bold"))

    drawer.goto(center_x, center_y - 20)
    drawer.pencolor(TEXT_COLOR)
    drawer.write("Press R to restart", align="center", font=("Courier", 12, "normal"))


def draw_pause_screen(drawer):
    """
    Display a pause screen that completely blanks out the playing field.
    This hides the board so the player can't study piece positions while paused.
    A large dark rectangle covers the entire board area.
    """
    # Draw a big filled rectangle over the entire board to hide all pieces
    draw_filled_rect(
        drawer,
        BOARD_LEFT, BOARD_TOP,
        BOARD_PIXEL_WIDTH, BOARD_PIXEL_HEIGHT,
        BACKGROUND_COLOR, BACKGROUND_COLOR
    )

    # Re-draw the border on top of the blanked board so it still looks tidy
    draw_board_border(drawer)

    # Show the "PAUSED" message centered on the now-blank board
    center_x = BOARD_LEFT + BOARD_PIXEL_WIDTH // 2
    center_y = 30

    # Draw a small box behind the text for readability
    draw_filled_rect(
        drawer,
        BOARD_LEFT + 20, center_y + 55,
        BOARD_PIXEL_WIDTH - 40, 90,
        "#0e0e20", "#4488ff"
    )

    drawer.penup()
    drawer.goto(center_x, center_y + 10)
    drawer.pencolor("#4488ff")
    drawer.write("PAUSED", align="center", font=("Courier", 22, "bold"))

    drawer.goto(center_x, center_y - 20)
    drawer.pencolor(TEXT_COLOR)
    drawer.write("Press Esc or P to resume", align="center", font=("Courier", 12, "normal"))


def draw_everything(drawer, game_state):
    """
    Redraw the entire game screen.
    We clear the screen and redraw from scratch each frame.
    The turtle 'tracer(0)' setting means nothing shows until we call 'update()'.
    """
    drawer.clear()

    # 1. Draw the grid lines (skip if paused — the board will be blanked)
    if not game_state["paused"]:
        draw_grid_lines(drawer)

    # 2. Draw the board border
    draw_board_border(drawer)

    # 3. Draw all locked blocks on the board (skip if paused — board is hidden)
    if not game_state["paused"]:
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                cell_color = game_state["board"][row][col]
                if cell_color is not None:
                    draw_block(drawer, row, col, cell_color)

    # 4. Draw the ghost piece (landing preview) — only during active play
    if not game_state["game_over"] and not game_state["paused"]:
        ghost_cells = get_ghost_position(game_state)
        for row, col in ghost_cells:
            draw_ghost_block(drawer, row, col)

    # 5. Draw the current falling piece — only during active play
    if game_state["current_piece"] and not game_state["game_over"] and not game_state["paused"]:
        for row, col in game_state["current_piece"]:
            if row >= 0:  # Only draw cells that are on the visible board
                draw_block(drawer, row, col, game_state["current_color"])

    # 6. Draw the info panel (score and controls are always visible,
    #    but hide the next piece preview when paused)
    if not game_state["paused"]:
        draw_next_piece_preview(drawer, game_state["next_type"])
    draw_score_info(drawer, game_state)
    draw_controls_help(drawer)

    # 7. Draw overlay messages if needed
    if game_state["game_over"]:
        draw_game_over(drawer)
    elif game_state["paused"]:
        draw_pause_screen(drawer)

    # Push all the drawing to the screen at once (fast, no flicker)
    screen.update()


# =============================================================================
# GAME LOGIC — The main game loop and input handlers
# =============================================================================

def game_tick():
    """
    This function runs repeatedly on a timer.
    Each tick, the piece falls down one row.
    If it can't fall, it locks in place and a new piece spawns.
    """
    if game["game_over"] or game["paused"]:
        draw_everything(drawer, game)
        screen.ontimer(game_tick, game["fall_speed"])
        return

    # Try to move the piece down
    moved = move_piece(game, 1, 0)

    if not moved:
        # The piece can't move down — lock it into the board
        lock_piece(game)

        # Check for and clear any completed lines
        lines = clear_full_lines(game)
        update_score(game, lines)

        # Spawn a new piece
        spawn_piece(game)

    # Redraw the screen
    draw_everything(drawer, game)

    # Schedule the next tick
    screen.ontimer(game_tick, game["fall_speed"])


def on_left():
    """Handle left arrow key press — move piece left."""
    if not game["game_over"] and not game["paused"]:
        move_piece(game, 0, -1)
        draw_everything(drawer, game)


def on_right():
    """Handle right arrow key press — move piece right."""
    if not game["game_over"] and not game["paused"]:
        move_piece(game, 0, 1)
        draw_everything(drawer, game)


def on_up():
    """Handle up arrow key press — rotate piece."""
    if not game["game_over"] and not game["paused"]:
        rotate_piece(game)
        draw_everything(drawer, game)


def on_down():
    """Handle down arrow key press — soft drop (move down one row)."""
    if not game["game_over"] and not game["paused"]:
        move_piece(game, 1, 0)
        draw_everything(drawer, game)


def on_space():
    """Handle space bar — hard drop (instantly drop piece to bottom)."""
    if not game["game_over"] and not game["paused"]:
        hard_drop(game)
        lock_piece(game)
        lines = clear_full_lines(game)
        update_score(game, lines)
        spawn_piece(game)
        draw_everything(drawer, game)


def on_pause():
    """Handle P key — toggle pause."""
    if not game["game_over"]:
        game["paused"] = not game["paused"]
        draw_everything(drawer, game)


def on_restart():
    """Handle R key — restart the game."""
    start_new_game()


def start_new_game():
    """Reset all game state and start a fresh game."""
    game["board"] = create_empty_board()
    game["score"] = 0
    game["level"] = 1
    game["lines_cleared"] = 0
    game["game_over"] = False
    game["paused"] = False
    game["fall_speed"] = INITIAL_FALL_SPEED
    game["current_piece"] = None
    game["current_offsets"] = []

    # Pick the first "next" piece, then spawn the first piece
    game["next_type"] = random.choice(list(TETROMINOES.keys()))
    spawn_piece(game)

    draw_everything(drawer, game)


# =============================================================================
# MAIN — Set up the window, create turtles, and start the game
# =============================================================================

# --- Set up the screen ---
screen = turtle.Screen()
screen.title("Tetris — Python Turtle Edition")
screen.bgcolor(BACKGROUND_COLOR)
screen.setup(
    width=BOARD_PIXEL_WIDTH + 280,
    height=BOARD_PIXEL_HEIGHT + 80
)
# Turn off automatic screen updates — we'll update manually for smooth drawing
screen.tracer(0)

# --- Create a turtle for drawing ---
# We hide the turtle cursor since we're only using it to draw shapes
drawer = turtle.Turtle()
drawer.hideturtle()
drawer.speed(0)       # Fastest drawing speed
drawer.pensize(1)

# --- Bind keyboard controls ---
# Arrow keys
screen.listen()
screen.onkeypress(on_left, "Left")
screen.onkeypress(on_right, "Right")
screen.onkeypress(on_up, "Up")
screen.onkeypress(on_down, "Down")

# WASD keys (duplicate bindings so either set works)
screen.onkeypress(on_left, "a")
screen.onkeypress(on_right, "d")
screen.onkeypress(on_up, "w")
screen.onkeypress(on_down, "s")

# Action keys
screen.onkeypress(on_space, "space")
screen.onkeypress(on_pause, "p")
screen.onkeypress(on_pause, "Escape")   # Escape also toggles pause
screen.onkeypress(on_restart, "r")

# --- Start the game! ---
start_new_game()
game_tick()

# Keep the window open until the user closes it
turtle.mainloop()
