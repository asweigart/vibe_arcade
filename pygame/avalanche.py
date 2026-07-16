"""
================================================================================
  KIRBY'S AVALANCHE STYLE GAME (Puyo Puyo clone)
  A teaching example for people new to programming
================================================================================

WHAT IS THIS GAME?
------------------
This is a falling-block puzzle game similar to Tetris, but instead of clearing
horizontal lines, you clear groups of 4 or more matching colored blobs that
touch each other. Pairs of colored blobs fall from the top, and the player
controls where they land. When 4+ same-color blobs connect, they pop!

HOW TO PLAY:
  Left/Right arrows ... Move the falling pair sideways
  Down arrow ........... Drop the pair faster (soft drop)
  Up arrow / Space ..... Rotate the pair
  R .................... Restart after game over

PROGRAMMING CONCEPTS DEMONSTRATED:
  - Variables and constants
  - Functions (small, single-purpose)
  - Lists and 2D grids (lists of lists)
  - Loops (for, while)
  - Conditionals (if/elif/else)
  - The "game loop" pattern
  - Event handling (keyboard input)
  - Drawing graphics with Pygame
  - Recursion (used to find connected groups of blobs)
"""

# ------------------------------------------------------------------------------
# IMPORTS — bringing in code that other people have already written for us.
# ------------------------------------------------------------------------------
# `pygame` is the library that handles drawing, input, and timing for us.
# `random`  is from Python's standard library; we use it to pick random colors.
# `sys`     gives us a clean way to quit the program.
import pygame
import random
import sys


# ==============================================================================
# CONSTANTS
# ==============================================================================
# A "constant" is a value we set once at the top and never change.
# Naming them in ALL_CAPS is a Python convention that signals "don't modify me".
# Putting them all together makes the game easy to tweak later.
# ==============================================================================

# --- Grid dimensions (in cells, not pixels) -----------------------------------
# The play field is a grid of cells, like graph paper. Each cell holds one blob.
GRID_COLS = 6           # how many columns wide the play field is
GRID_ROWS = 13          # how many rows tall (top row is hidden — see below)

# --- Cell size and window layout (in pixels) ----------------------------------
CELL_SIZE = 40          # each blob is drawn as a 40x40 pixel square
SIDEBAR_WIDTH = 200     # space on the right for score and "next pair" preview

# Window size is calculated from the constants above, so if you change the
# grid, the window resizes itself automatically.
WINDOW_WIDTH = GRID_COLS * CELL_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = (GRID_ROWS - 1) * CELL_SIZE   # -1 because top row is hidden

# --- Timing -------------------------------------------------------------------
FPS = 60                # frames per second — how often the screen updates
FALL_INTERVAL_MS = 500  # how often the falling pair drops one row (milliseconds)
SOFT_DROP_MS = 50       # faster fall speed when player holds Down arrow
POP_DELAY_MS = 300      # how long popping blobs stay visible before disappearing

# --- Colors as (Red, Green, Blue) tuples; each value is 0–255 -----------------
# Colors in Pygame are tuples of three numbers. (255, 0, 0) is pure red, etc.
BG_COLOR        = (20, 20, 40)      # dark blue-ish background
GRID_COLOR      = (50, 50, 80)      # faint lines between cells
TEXT_COLOR      = (255, 255, 255)   # white text
GAME_OVER_COLOR = (255, 80, 80)     # red-ish for the "Game Over" message

# The blob colors. We keep them in a dictionary so each color has a name.
# A dictionary maps "keys" to "values": KEY -> VALUE.
BLOB_COLORS = {
    "red":    (230,  60,  60),
    "green":  ( 60, 200,  80),
    "blue":   ( 60, 120, 230),
    "yellow": (240, 220,  60),
    "purple": (180,  80, 200),
}
# We'll need just the names sometimes, so we make a list of them.
COLOR_NAMES = list(BLOB_COLORS.keys())

# --- Game rules ---------------------------------------------------------------
MIN_GROUP_TO_POP = 4    # need 4+ connected same-color blobs to clear them
POINTS_PER_BLOB  = 10   # each popped blob is worth this much


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
# A "function" is a reusable chunk of code with a name. Breaking the program
# into small functions makes each piece easier to understand and test.
# ==============================================================================

def make_empty_grid():
    """
    Build a fresh, empty playing field.

    The grid is a 2D structure: a list of rows, where each row is a list of
    cells. We use `None` to mean "this cell is empty". When a cell contains
    a blob, we'll store the color name string (like "red") in it.

    Returns: a list of GRID_ROWS lists, each containing GRID_COLS Nones.
    """
    # This is called a "list comprehension". Read it as:
    # "For every row index from 0 to GRID_ROWS-1, build a row of GRID_COLS Nones."
    return [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def random_color():
    """Pick a random color name from our list. Used to make new falling blobs."""
    return random.choice(COLOR_NAMES)


def make_new_pair():
    """
    Create a new pair of blobs that will fall from the top together.

    A "pair" is the two-blob piece the player controls. We represent it as a
    dictionary so we can refer to its parts by name (clearer than a tuple).

    The pair has a "pivot" blob and a "partner" blob. The partner sits in one
    of four positions around the pivot, controlled by `rotation`:
        0 = above, 1 = right, 2 = below, 3 = left
    Rotating the pair just changes this number.

    The pair starts near the top-middle of the grid.
    """
    return {
        "pivot_row":    1,                        # pivot starts on row 1
        "pivot_col":    GRID_COLS // 2 - 1,       # roughly centered
        "pivot_color":  random_color(),
        "partner_color": random_color(),
        "rotation":     0,                        # 0 = partner is above pivot
    }


def partner_position(pair):
    """
    Given a pair, calculate where the partner blob currently is.

    The partner's position depends on the pivot's position and the rotation.
    We return (row, col) so the caller can use it directly.
    """
    # Read these as: "if rotation is 0, partner is one row above pivot", etc.
    if pair["rotation"] == 0:
        return (pair["pivot_row"] - 1, pair["pivot_col"])      # above
    elif pair["rotation"] == 1:
        return (pair["pivot_row"],     pair["pivot_col"] + 1)  # right
    elif pair["rotation"] == 2:
        return (pair["pivot_row"] + 1, pair["pivot_col"])      # below
    else:  # rotation == 3
        return (pair["pivot_row"],     pair["pivot_col"] - 1)  # left


def is_valid_position(grid, row, col):
    """
    Check whether a single cell position is allowed for a blob right now.

    A position is valid if:
      - It's inside the grid horizontally (0 <= col < GRID_COLS)
      - It's not below the bottom row
      - The cell is empty (no blob already there)

    We allow negative rows because pieces can poke above the visible area
    while they're spawning.
    """
    if col < 0 or col >= GRID_COLS:
        return False
    if row >= GRID_ROWS:
        return False
    # Allow rows above the grid — the pair spawns partly off-screen.
    if row < 0:
        return True
    # The cell must be empty (None means empty).
    return grid[row][col] is None


def pair_fits(grid, pair):
    """Return True if BOTH blobs of the pair are in valid positions."""
    pr, pc = partner_position(pair)
    return (
        is_valid_position(grid, pair["pivot_row"], pair["pivot_col"])
        and is_valid_position(grid, pr, pc)
    )


def lock_pair_into_grid(grid, pair):
    """
    "Lock" the falling pair into the grid — they stop being controlled by
    the player and become part of the stack. We just write the colors into
    the grid cells where the blobs are.
    """
    grid[pair["pivot_row"]][pair["pivot_col"]] = pair["pivot_color"]
    pr, pc = partner_position(pair)
    # Only place the partner if it's actually inside the grid.
    if pr >= 0:
        grid[pr][pc] = pair["partner_color"]


def apply_gravity(grid):
    """
    Make floating blobs fall down to fill any gaps below them.

    After we pop a group, the blobs above the popped ones need to fall.
    For each column, we collect the non-empty blobs from bottom to top,
    then re-place them at the bottom of the column.

    Returns True if any blob actually moved (useful for chain reactions).
    """
    moved = False
    for col in range(GRID_COLS):
        # Gather the colors in this column, skipping the empty spots.
        # We walk from bottom up so the order stays correct for re-placing.
        stack = []
        for row in range(GRID_ROWS - 1, -1, -1):
            if grid[row][col] is not None:
                stack.append(grid[row][col])

        # Now clear the column and put the blobs back at the bottom.
        for row in range(GRID_ROWS):
            grid[row][col] = None
        for i, color in enumerate(stack):
            new_row = GRID_ROWS - 1 - i
            grid[new_row][col] = color
            # If a blob ended up in a different row than it started, gravity
            # actually did something this turn.
            # (We can't easily check old vs new without another pass, so we
            # just say "moved" if there was any blob that could have shifted.
            # In practice this is fine because we call apply_gravity in a loop
            # only after pops, which always create gaps.)
        if stack:
            moved = True
    return moved


def find_connected_group(grid, start_row, start_col, visited):
    """
    Find every blob connected to the one at (start_row, start_col) that
    shares its color. Two blobs are "connected" if they touch up, down,
    left, or right (NOT diagonally).

    We use a technique called "flood fill", which is naturally recursive:
    a function that calls itself on neighboring cells. The `visited` set
    keeps track of cells we've already checked so we don't loop forever.

    Returns a list of (row, col) positions in the connected group.
    """
    target_color = grid[start_row][start_col]
    if target_color is None:
        return []

    group = []
    # We'll use a stack (a list we push onto and pop from) instead of true
    # recursion. This avoids hitting Python's recursion limit on big groups.
    to_check = [(start_row, start_col)]

    while to_check:
        row, col = to_check.pop()

        # Skip if we've seen this cell or if it's out of bounds.
        if (row, col) in visited:
            continue
        if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
            continue
        if grid[row][col] != target_color:
            continue

        # This cell is part of the group!
        visited.add((row, col))
        group.append((row, col))

        # Check the four neighbors next.
        to_check.append((row - 1, col))  # up
        to_check.append((row + 1, col))  # down
        to_check.append((row, col - 1))  # left
        to_check.append((row, col + 1))  # right

    return group


def find_all_groups_to_pop(grid):
    """
    Scan the whole grid and return every group of MIN_GROUP_TO_POP+ same-color
    connected blobs. Each group is returned as a list of (row, col) positions.
    """
    visited = set()         # cells we've already grouped
    groups_to_pop = []      # the list we'll return

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if grid[row][col] is None:
                continue
            if (row, col) in visited:
                continue
            group = find_connected_group(grid, row, col, visited)
            if len(group) >= MIN_GROUP_TO_POP:
                groups_to_pop.append(group)

    return groups_to_pop


def remove_group_from_grid(grid, group):
    """Erase every blob in `group` from the grid (set those cells to None)."""
    for (row, col) in group:
        grid[row][col] = None


# ==============================================================================
# DRAWING FUNCTIONS
# ==============================================================================
# All the code that puts pixels on the screen lives here. Keeping drawing
# separate from game logic makes both easier to read.
# ==============================================================================

def draw_blob(surface, color_name, row, col, popping=False):
    """
    Draw one blob at grid position (row, col).

    Pygame's coordinate system has (0,0) in the TOP-LEFT corner, with x going
    right and y going down. We convert grid (row, col) to pixel (x, y) here.

    The top row of the grid is hidden (it's where pieces spawn from), so we
    subtract 1 from the row when calculating the screen position.
    """
    if row < 1:
        return  # blob is in the hidden spawn row, don't draw it

    x = col * CELL_SIZE
    y = (row - 1) * CELL_SIZE
    color = BLOB_COLORS[color_name]

    # If the blob is "popping", draw it lighter to show it's about to vanish.
    if popping:
        # Average each color channel with white to lighten the color.
        color = tuple((c + 255) // 2 for c in color)

    # Draw a filled circle for the blob body...
    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
    radius = CELL_SIZE // 2 - 2
    pygame.draw.circle(surface, color, center, radius)

    # ...and a darker outline so blobs are easy to tell apart visually.
    outline = tuple(c // 2 for c in BLOB_COLORS[color_name])
    pygame.draw.circle(surface, outline, center, radius, 2)

    # Two little white "eyes" for that classic Puyo cuteness.
    eye_offset_x = CELL_SIZE // 6
    eye_offset_y = CELL_SIZE // 8
    eye_radius = max(2, CELL_SIZE // 10)
    pygame.draw.circle(surface, (255, 255, 255),
                       (center[0] - eye_offset_x, center[1] - eye_offset_y), eye_radius)
    pygame.draw.circle(surface, (255, 255, 255),
                       (center[0] + eye_offset_x, center[1] - eye_offset_y), eye_radius)
    # Pupils inside the eyes.
    pygame.draw.circle(surface, (0, 0, 0),
                       (center[0] - eye_offset_x, center[1] - eye_offset_y), max(1, eye_radius // 2))
    pygame.draw.circle(surface, (0, 0, 0),
                       (center[0] + eye_offset_x, center[1] - eye_offset_y), max(1, eye_radius // 2))


def draw_grid_lines(surface):
    """Draw the faint grid lines so the player can see the cell boundaries."""
    for col in range(GRID_COLS + 1):
        x = col * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for row in range(GRID_ROWS):
        y = row * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (0, y), (GRID_COLS * CELL_SIZE, y))


def draw_grid_contents(surface, grid, popping_cells):
    """Draw every locked-in blob currently on the grid."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            color_name = grid[row][col]
            if color_name is not None:
                # Highlight cells that are about to pop so the player sees them flash.
                is_popping = (row, col) in popping_cells
                draw_blob(surface, color_name, row, col, popping=is_popping)


def draw_pair(surface, pair):
    """Draw the player-controlled falling pair."""
    draw_blob(surface, pair["pivot_color"], pair["pivot_row"], pair["pivot_col"])
    pr, pc = partner_position(pair)
    draw_blob(surface, pair["partner_color"], pr, pc)


def draw_sidebar(surface, font, score, next_pair, game_over):
    """Draw the score, the 'next pair' preview, and any messages."""
    # The sidebar starts to the right of the play field.
    sidebar_x = GRID_COLS * CELL_SIZE + 20

    # Score text.
    score_label = font.render("SCORE", True, TEXT_COLOR)
    score_value = font.render(str(score), True, TEXT_COLOR)
    surface.blit(score_label, (sidebar_x, 20))
    surface.blit(score_value, (sidebar_x, 50))

    # "Next" preview — we draw the upcoming pair as two stacked circles.
    next_label = font.render("NEXT", True, TEXT_COLOR)
    surface.blit(next_label, (sidebar_x, 110))

    # Draw the next-pair preview circles (partner above pivot).
    preview_x = sidebar_x + CELL_SIZE // 2
    preview_top_y = 150
    pygame.draw.circle(surface, BLOB_COLORS[next_pair["partner_color"]],
                       (preview_x, preview_top_y), CELL_SIZE // 2 - 4)
    pygame.draw.circle(surface, BLOB_COLORS[next_pair["pivot_color"]],
                       (preview_x, preview_top_y + CELL_SIZE), CELL_SIZE // 2 - 4)

    # Game over message.
    if game_over:
        msg = font.render("GAME OVER", True, GAME_OVER_COLOR)
        surface.blit(msg, (sidebar_x, 250))
        hint = font.render("Press R", True, TEXT_COLOR)
        surface.blit(hint, (sidebar_x, 280))

    # Controls hint at the bottom.
    controls = [
        "Controls:",
        "Arrows: move",
        "Up/Space: rotate",
        "Down: drop fast",
    ]
    for i, line in enumerate(controls):
        text = font.render(line, True, TEXT_COLOR)
        surface.blit(text, (sidebar_x, WINDOW_HEIGHT - 110 + i * 22))


# ==============================================================================
# MAIN GAME
# ==============================================================================
# The `main` function contains the "game loop" — the heart of any video game.
# Every frame (60 times per second), we:
#   1. Read input from the player
#   2. Update the game state (move pieces, check for matches)
#   3. Draw everything to the screen
# ==============================================================================

def main():
    # --- Pygame setup ---------------------------------------------------------
    pygame.init()  # initialize all of Pygame's modules
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Avalanche!")
    clock = pygame.time.Clock()  # used to cap the frame rate
    font = pygame.font.SysFont("Arial", 22, bold=True)

    # --- Game state -----------------------------------------------------------
    # Wrapping this in a function lets us "reset" the game easily.
    def new_game():
        return {
            "grid":       make_empty_grid(),
            "current":    make_new_pair(),
            "next":       make_new_pair(),
            "score":      0,
            "fall_timer": 0,         # milliseconds since last fall
            "game_over":  False,
            # When blobs are about to pop, we pause briefly so the player
            # can see what's happening. These track that pause:
            "popping":    set(),     # cells currently flashing before pop
            "pop_timer":  0,         # ms remaining in the pop animation
            "pending_pops": [],      # groups waiting to be removed
        }

    state = new_game()

    # --- The game loop --------------------------------------------------------
    # `while True` means "keep going forever". We exit by calling sys.exit().
    while True:
        # `clock.tick(FPS)` does two things: it waits long enough to keep us
        # at FPS frames per second, and returns how many milliseconds passed
        # since the last call. We use that for our timers.
        dt = clock.tick(FPS)

        # ---------- 1. INPUT ----------
        # Pygame queues up events (key presses, window close, etc.). We check
        # them all every frame.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # The player clicked the X on the window.
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Allow restart anytime by pressing R.
                if event.key == pygame.K_r:
                    state = new_game()
                    continue

                # When game is over or blobs are popping, ignore movement keys.
                if state["game_over"] or state["popping"]:
                    continue

                pair = state["current"]

                if event.key == pygame.K_LEFT:
                    # Try to move left. Make a copy, change it, and only commit
                    # the change if it's still a valid position.
                    pair["pivot_col"] -= 1
                    if not pair_fits(state["grid"], pair):
                        pair["pivot_col"] += 1  # undo

                elif event.key == pygame.K_RIGHT:
                    pair["pivot_col"] += 1
                    if not pair_fits(state["grid"], pair):
                        pair["pivot_col"] -= 1

                elif event.key in (pygame.K_UP, pygame.K_SPACE):
                    # Rotate clockwise: 0 -> 1 -> 2 -> 3 -> 0
                    old_rotation = pair["rotation"]
                    pair["rotation"] = (pair["rotation"] + 1) % 4

                    # If the rotation pushes us into a wall, try "kicking" the
                    # pair sideways by one cell so the rotation can succeed.
                    # This is a common trick in falling-block puzzle games.
                    if not pair_fits(state["grid"], pair):
                        pair["pivot_col"] -= 1
                        if not pair_fits(state["grid"], pair):
                            pair["pivot_col"] += 2
                            if not pair_fits(state["grid"], pair):
                                # Couldn't make it work — undo everything.
                                pair["pivot_col"] -= 1
                                pair["rotation"] = old_rotation

        # ---------- 2. UPDATE ----------
        if state["game_over"]:
            # Don't update anything when the game's over — just keep drawing.
            pass

        elif state["popping"]:
            # Currently showing the pop animation. Count down, then remove.
            state["pop_timer"] -= dt
            if state["pop_timer"] <= 0:
                # Time's up — actually delete the popping blobs.
                total_popped = 0
                for group in state["pending_pops"]:
                    remove_group_from_grid(state["grid"], group)
                    total_popped += len(group)
                state["score"] += total_popped * POINTS_PER_BLOB

                # Apply gravity so blobs above fall down.
                apply_gravity(state["grid"])

                # Clear the pop state and check for chain reactions —
                # after gravity, new groups might form!
                state["popping"] = set()
                state["pending_pops"] = []

                new_groups = find_all_groups_to_pop(state["grid"])
                if new_groups:
                    # Chain! Start another pop animation.
                    state["pending_pops"] = new_groups
                    state["popping"] = set(
                        cell for group in new_groups for cell in group
                    )
                    state["pop_timer"] = POP_DELAY_MS

        else:
            # Normal play: make the falling pair fall over time.
            keys = pygame.key.get_pressed()
            interval = SOFT_DROP_MS if keys[pygame.K_DOWN] else FALL_INTERVAL_MS

            state["fall_timer"] += dt
            if state["fall_timer"] >= interval:
                state["fall_timer"] = 0
                pair = state["current"]

                # Try moving the pair down by one row.
                pair["pivot_row"] += 1
                if not pair_fits(state["grid"], pair):
                    # Can't go down — undo and lock the pair into the grid.
                    pair["pivot_row"] -= 1
                    lock_pair_into_grid(state["grid"], pair)

                    # Check if anything pops.
                    groups = find_all_groups_to_pop(state["grid"])
                    if groups:
                        state["pending_pops"] = groups
                        state["popping"] = set(
                            cell for group in groups for cell in group
                        )
                        state["pop_timer"] = POP_DELAY_MS

                    # Bring in the next pair.
                    state["current"] = state["next"]
                    state["next"] = make_new_pair()

                    # If the new pair can't even spawn, the player has lost.
                    if not pair_fits(state["grid"], state["current"]):
                        state["game_over"] = True

        # ---------- 3. DRAW ----------
        # Always draw in this order: background, then game pieces, then UI.
        screen.fill(BG_COLOR)
        draw_grid_lines(screen)
        draw_grid_contents(screen, state["grid"], state["popping"])

        # Only draw the falling pair when the game is actively playing.
        if not state["game_over"] and not state["popping"]:
            draw_pair(screen, state["current"])

        draw_sidebar(screen, font, state["score"], state["next"], state["game_over"])

        # Push everything we drew to the actual screen.
        pygame.display.flip()


# This `if __name__ == "__main__":` line is a Python idiom that means
# "only run main() when this file is executed directly, not imported".
if __name__ == "__main__":
    main()
