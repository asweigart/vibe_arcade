"""
================================================================================
SIMPLE SNOOD GAME
================================================================================
A bubble-shooter style game inspired by the classic Snood (1996).

HOW TO PLAY:
- Aim the launcher at the bottom of the screen with your mouse.
- Click the left mouse button to shoot a snood (colored ball).
- When 3 or more snoods of the same color touch, they pop and disappear.
- Any snoods left "floating" (not connected to the top) also fall and pop.
- Clear all the snoods to win!
- If snoods reach the bottom danger line, you lose.

REQUIREMENTS:
- Python 3.x
- pygame  (install with: pip install pygame)

RUN:
- python snood.py

This file uses NO external assets — all graphics are drawn with pygame primitives.
================================================================================
"""

import pygame      # The graphics/game library that does all the heavy lifting.
import math        # We need sin/cos for aiming the launcher and moving the snood.
import random      # We use this to pick random colors for new snoods.
import sys         # Used to cleanly exit the program.


# =============================================================================
# CONSTANTS — TWEAK THESE TO CHANGE THE FEEL OF THE GAME
# =============================================================================
# All the "magic numbers" that control the game live up here in one place.
# Changing them will alter difficulty, appearance, speed, etc. Comments next
# to each one suggest interesting things to try.

# ---- Window / display ----
SCREEN_WIDTH  = 480              # Window width in pixels. Try 600 for a wider playfield.
SCREEN_HEIGHT = 640              # Window height in pixels. Taller = more reaction time.
FPS           = 60               # Frames per second. 60 is smooth; 30 is choppier but lighter.
WINDOW_TITLE  = "Simple Snood"   # Text shown in the window's title bar.

# ---- Snood (ball) sizing ----
# The grid is built around the snood radius. Changing SNOOD_RADIUS rescales the
# whole playfield, so you may want to adjust SCREEN_WIDTH to match.
SNOOD_RADIUS  = 18               # Radius of each snood in pixels. Try 14 (harder) or 22 (easier).
SNOOD_DIAMETER = SNOOD_RADIUS * 2  # Helper — don't change this directly.

# Hex-grid spacing. Snoods sit in a honeycomb pattern; every other row is
# offset horizontally by one radius. The vertical spacing between rows is
# slightly less than the diameter so neighbors actually touch.
ROW_HEIGHT    = int(SNOOD_DIAMETER * 0.87)  # 0.87 ≈ sqrt(3)/2, the math for hex grids.

# ---- Grid (the field of snoods at the top) ----
GRID_COLS     = SCREEN_WIDTH // SNOOD_DIAMETER   # How many snoods fit per row.
START_ROWS    = 6                # How many filled rows the level starts with. Try 4 (easy) or 9 (hard).
GRID_TOP      = 40               # Pixels from the top of the screen to the first row.
DANGER_ROW_Y  = SCREEN_HEIGHT - 100  # If any snood touches this Y, you lose. Lower = more lenient.

# ---- Launcher (where new snoods are fired from) ----
LAUNCHER_X    = SCREEN_WIDTH // 2          # X position of the launcher (center of the screen).
LAUNCHER_Y    = SCREEN_HEIGHT - 40         # Y position of the launcher (near the bottom).
LAUNCHER_LENGTH = 40                       # Length of the aiming line. Cosmetic.
SHOT_SPEED    = 12                         # How fast a fired snood moves (pixels/frame).
                                           #   Try 8 (slow & easy) or 18 (twitchy).
MIN_AIM_ANGLE = math.radians(15)           # Limits aiming so you can't shoot sideways/down.
                                           #   Smaller = more freedom; larger = more restricted.

# ---- Match / scoring rules ----
MATCH_MIN     = 3                # Snoods of the same color needed to pop. Classic Snood = 3.

# ---- Colors ----
# pygame uses (Red, Green, Blue) tuples, each value 0–255.
# Add or remove tuples here to change how many colors are in play. Fewer colors = easier.
SNOOD_COLORS = [
    (230,  60,  60),   # red
    ( 60, 160, 230),   # blue
    ( 80, 200,  90),   # green
    (240, 210,  60),   # yellow
    (200,  90, 220),   # purple
]
# Try cutting this list down to 3 colors for a much easier game,
# or adding two more for a much harder one.

# Background and UI colors. Tweak freely for a different look.
BG_TOP_COLOR    = ( 20,  24,  40)   # Top of the gradient background.
BG_BOTTOM_COLOR = ( 50,  30,  70)   # Bottom of the gradient background.
WALL_COLOR      = (200, 200, 220)   # Side walls.
DANGER_COLOR    = (220,  60,  60)   # Color of the "you lose" line.
TEXT_COLOR      = (240, 240, 240)   # Default UI text color.
LAUNCHER_COLOR  = (220, 220, 220)   # Color of the aiming line.

# ---- Visuals ----
HIGHLIGHT_OFFSET = SNOOD_RADIUS // 3   # Where the shiny highlight sits on each snood.
HIGHLIGHT_RADIUS = SNOOD_RADIUS // 3   # Size of the shiny highlight.


# =============================================================================
# GRID HELPER FUNCTIONS
# =============================================================================
# The playfield is a 2D grid of cells. Each cell can be empty (None) or hold a
# color. Because every other row is offset, we need helpers to convert between
# grid coordinates (row, col) and screen pixel coordinates (x, y).

def is_offset_row(row):
    """Return True if `row` is one of the indented rows in the hex grid.

    Rows 0, 2, 4, ... are flush with the left wall.
    Rows 1, 3, 5, ... are pushed right by one radius so the snoods nest.
    """
    return row % 2 == 1


def cells_in_row(row):
    """How many snoods fit in a given row.

    Offset rows lose one slot because of the indent.
    """
    return GRID_COLS - 1 if is_offset_row(row) else GRID_COLS


def grid_to_pixel(row, col):
    """Convert a (row, col) grid cell into the (x, y) center pixel of that cell."""
    # Start at the left wall, plus a radius so the first snood is fully on-screen.
    x = col * SNOOD_DIAMETER + SNOOD_RADIUS
    if is_offset_row(row):
        x += SNOOD_RADIUS  # Indent every other row.
    y = GRID_TOP + row * ROW_HEIGHT + SNOOD_RADIUS
    return x, y


def pixel_to_nearest_cell(x, y, grid):
    """Find the empty grid cell whose center is closest to the pixel (x, y).

    This is used when a flying snood collides with something — we need to
    decide which grid slot it should "snap" into.
    """
    # First, estimate the row from the y-coordinate. Round to the nearest row.
    row = round((y - GRID_TOP - SNOOD_RADIUS) / ROW_HEIGHT)
    # Don't let the snood snap above the top of the grid.
    if row < 0:
        row = 0

    # Make sure the row exists in our grid (extend the grid downward if needed).
    while row >= len(grid):
        grid.append([None] * cells_in_row(len(grid)))

    # Now estimate the column based on x. Account for the row indent.
    x_offset = SNOOD_RADIUS * 2 if is_offset_row(row) else SNOOD_RADIUS
    col = round((x - x_offset) / SNOOD_DIAMETER)

    # Clamp the column so it stays in bounds for this row.
    max_col = cells_in_row(row) - 1
    col = max(0, min(col, max_col))

    # If our first guess is occupied, try nearby cells. This stops a fast-moving
    # snood from "stealing" a slot that's already taken.
    if grid[row][col] is not None:
        # Check left, right, and the row below for a free slot.
        candidates = [
            (row, col - 1),
            (row, col + 1),
            (row + 1, col),
            (row + 1, col - 1),
        ]
        for r, c in candidates:
            if r < 0:
                continue
            while r >= len(grid):
                grid.append([None] * cells_in_row(len(grid)))
            if 0 <= c < cells_in_row(r) and grid[r][c] is None:
                return r, c
    return row, col


def neighbors(row, col):
    """Return the (row, col) of all six hex-grid neighbors of this cell.

    A hex cell has 6 neighbors: left, right, and 2 each above and below. The
    above/below neighbors depend on whether we're on an offset row or not.
    """
    if is_offset_row(row):
        # On offset (indented) rows, the upper/lower neighbors are at col and col+1.
        deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    else:
        # On non-offset rows, they're at col-1 and col.
        deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    return [(row + dr, col + dc) for dr, dc in deltas]


def valid_cell(grid, row, col):
    """Return True if (row, col) is inside the current grid."""
    if row < 0 or row >= len(grid):
        return False
    if col < 0 or col >= cells_in_row(row):
        return False
    return True


# =============================================================================
# MATCH-FINDING (FLOOD FILL)
# =============================================================================
# When a snood lands, we need to find every connected cell of the same color.
# This is a classic "flood fill" — start from one cell, walk to neighbors of
# the same color, repeat until you can't go any further.

def find_matching_group(grid, start_row, start_col):
    """Return a set of (row, col) cells connected to start with the same color."""
    color = grid[start_row][start_col]
    if color is None:
        return set()

    visited = set()
    stack = [(start_row, start_col)]   # Cells we still need to check.
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        if not valid_cell(grid, r, c):
            continue
        if grid[r][c] != color:
            continue
        visited.add((r, c))
        # Add all 6 neighbors to the to-do list.
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in visited:
                stack.append((nr, nc))
    return visited


def find_floating_snoods(grid):
    """Return all cells that are NOT connected to the top row.

    The top row is the "ceiling" — anything attached to it (directly or via
    other snoods) is safe. Anything else is floating in mid-air and should
    fall away. We do this by flood-filling from every top-row cell, then
    flagging anything we missed.
    """
    attached = set()
    stack = []
    # Seed the search with every non-empty cell in row 0.
    if len(grid) > 0:
        for col in range(cells_in_row(0)):
            if grid[0][col] is not None:
                stack.append((0, col))

    # Standard flood fill, but this time we don't care about color —
    # any non-empty neighbor counts as "still attached".
    while stack:
        r, c = stack.pop()
        if (r, c) in attached:
            continue
        if not valid_cell(grid, r, c):
            continue
        if grid[r][c] is None:
            continue
        attached.add((r, c))
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in attached:
                stack.append((nr, nc))

    # Anything filled but not in `attached` is floating.
    floating = set()
    for r in range(len(grid)):
        for c in range(cells_in_row(r)):
            if grid[r][c] is not None and (r, c) not in attached:
                floating.add((r, c))
    return floating


# =============================================================================
# DRAWING HELPERS
# =============================================================================

def draw_snood(surface, x, y, color):
    """Draw a single snood (a colored ball with a small highlight)."""
    # Main body.
    pygame.draw.circle(surface, color, (int(x), int(y)), SNOOD_RADIUS)
    # Darker outline so adjacent snoods are easier to tell apart.
    pygame.draw.circle(surface, (0, 0, 0), (int(x), int(y)), SNOOD_RADIUS, 1)
    # Glossy highlight in the upper-left, like a shiny marble.
    highlight_pos = (int(x) - HIGHLIGHT_OFFSET, int(y) - HIGHLIGHT_OFFSET)
    pygame.draw.circle(surface, (255, 255, 255), highlight_pos, HIGHLIGHT_RADIUS)


def draw_background(surface):
    """Paint a vertical gradient background across the whole screen."""
    # We draw one horizontal line per row of pixels, blending top to bottom.
    # This is cheap and produces a nicer look than a flat color.
    for y in range(SCREEN_HEIGHT):
        # 't' goes from 0.0 at the top to 1.0 at the bottom.
        t = y / SCREEN_HEIGHT
        r = int(BG_TOP_COLOR[0] * (1 - t) + BG_BOTTOM_COLOR[0] * t)
        g = int(BG_TOP_COLOR[1] * (1 - t) + BG_BOTTOM_COLOR[1] * t)
        b = int(BG_TOP_COLOR[2] * (1 - t) + BG_BOTTOM_COLOR[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))


def draw_text(surface, text, size, x, y, color=TEXT_COLOR, center=True):
    """Render `text` and blit it to `surface`. Returns the bounding rect."""
    # Using the default pygame font means we don't need any external font files.
    font = pygame.font.Font(None, size)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)
    return rect


# =============================================================================
# THE GAME ITSELF
# =============================================================================

class SnoodGame:
    """Holds all the game state and runs the main loop."""

    def __init__(self):
        pygame.init()                                                  # Boot pygame.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()                               # For locking the FPS.
        self.reset()                                                   # Set up a fresh game.

    # --- State management ---------------------------------------------------

    def reset(self):
        """(Re)initialize all the per-game state. Called on start and on R-key."""
        # Build the starting grid: a 2D list where each cell is a color tuple
        # or None for empty.
        self.grid = []
        for row in range(START_ROWS):
            row_cells = []
            for _ in range(cells_in_row(row)):
                row_cells.append(random.choice(SNOOD_COLORS))
                # Try this for an easier opening: if random.random() < 0.7, else None.
            self.grid.append(row_cells)

        # The snood currently sitting in the launcher waiting to be fired.
        self.current_color = self._pick_next_color()
        # The next snood after that, shown as a preview.
        self.next_color    = self._pick_next_color()

        # If a snood is currently in flight, store its (x, y, dx, dy, color).
        # Otherwise this is None.
        self.flying = None

        self.score      = 0
        self.game_over  = False
        self.win        = False

    def _pick_next_color(self):
        """Pick a color, biased toward colors still on the board.

        Picking a color that doesn't exist on the board feels really unfair, so
        if we can, we choose only from colors currently in play.
        """
        active_colors = set()
        for row in self.grid:
            for cell in row:
                if cell is not None:
                    active_colors.add(cell)
        if not active_colors:
            # The board is empty — anything goes.
            return random.choice(SNOOD_COLORS)
        return random.choice(list(active_colors))

    # --- Input handling -----------------------------------------------------

    def aim_angle_to(self, mx, my):
        """Compute the launcher angle that points at the mouse position (mx, my).

        Returns an angle measured CLOCKWISE from straight-up, in radians.
        Negative = aim left, positive = aim right.
        We clamp it so the player can't aim sideways or backwards.
        """
        dx = mx - LAUNCHER_X
        dy = LAUNCHER_Y - my   # Flip y because screen y grows downward.
        # atan2 of (dx, dy) gives the angle from +y axis (up), clockwise.
        angle = math.atan2(dx, dy)
        # Limit how far you can aim sideways. Pi/2 - MIN_AIM_ANGLE is the max.
        max_angle = math.pi / 2 - MIN_AIM_ANGLE
        return max(-max_angle, min(max_angle, angle))

    def fire(self, mx, my):
        """Launch the current snood toward the mouse position."""
        if self.flying is not None or self.game_over:
            return                       # Can't fire while one's already in the air.
        angle = self.aim_angle_to(mx, my)
        # Convert the angle into x and y velocity components.
        # sin(angle) gives sideways speed, cos(angle) gives upward speed.
        vx =  math.sin(angle) * SHOT_SPEED
        vy = -math.cos(angle) * SHOT_SPEED  # Negative y = upward on screen.
        self.flying = {
            'x': float(LAUNCHER_X),
            'y': float(LAUNCHER_Y),
            'vx': vx,
            'vy': vy,
            'color': self.current_color,
        }
        # Roll the next snood into the chamber.
        self.current_color = self.next_color
        self.next_color    = self._pick_next_color()

    # --- Update step --------------------------------------------------------

    def update(self):
        """Advance the game by one frame."""
        if self.game_over:
            return
        if self.flying is None:
            return                       # Nothing moving; nothing to update.

        # Move the flying snood.
        self.flying['x'] += self.flying['vx']
        self.flying['y'] += self.flying['vy']

        # Bounce off the left wall.
        if self.flying['x'] - SNOOD_RADIUS < 0:
            self.flying['x']  = SNOOD_RADIUS
            self.flying['vx'] = -self.flying['vx']
        # Bounce off the right wall.
        if self.flying['x'] + SNOOD_RADIUS > SCREEN_WIDTH:
            self.flying['x']  = SCREEN_WIDTH - SNOOD_RADIUS
            self.flying['vx'] = -self.flying['vx']

        # Did it hit the ceiling or another snood?
        if self.flying['y'] - SNOOD_RADIUS <= GRID_TOP or self._collides_with_grid():
            self._attach_flying_snood()

    def _collides_with_grid(self):
        """Return True if the flying snood overlaps any snood already on the board."""
        fx, fy = self.flying['x'], self.flying['y']
        # Two circles collide when the distance between their centers is less
        # than the sum of their radii. Both radii here are SNOOD_RADIUS, so we
        # compare against SNOOD_DIAMETER.
        # We square the distances so we don't need the (slow) sqrt.
        threshold = SNOOD_DIAMETER * SNOOD_DIAMETER
        for r in range(len(self.grid)):
            for c in range(cells_in_row(r)):
                if self.grid[r][c] is None:
                    continue
                gx, gy = grid_to_pixel(r, c)
                dx = fx - gx
                dy = fy - gy
                if dx * dx + dy * dy < threshold:
                    return True
        return False

    def _attach_flying_snood(self):
        """Snap the flying snood to the grid and process matches."""
        # Find the best empty cell to drop it into.
        row, col = pixel_to_nearest_cell(self.flying['x'], self.flying['y'], self.grid)
        # Make sure the row actually has space for this column (offset rows are shorter).
        if col >= cells_in_row(row):
            col = cells_in_row(row) - 1
        self.grid[row][col] = self.flying['color']
        self.flying = None              # The snood has landed.

        # Look for a same-color group of MATCH_MIN or more.
        group = find_matching_group(self.grid, row, col)
        if len(group) >= MATCH_MIN:
            # Pop the matched group.
            for r, c in group:
                self.grid[r][c] = None
            self.score += len(group)
            # Removing a chunk can leave other snoods floating with nothing
            # holding them up — drop those too, and award bonus points.
            floating = find_floating_snoods(self.grid)
            for r, c in floating:
                self.grid[r][c] = None
            self.score += len(floating) * 2   # Bonus: 2 points per dropped snood.

        # Win/lose checks.
        if self._board_is_empty():
            self.win = True
            self.game_over = True
        elif self._reached_danger_line():
            self.game_over = True

    def _board_is_empty(self):
        """Return True if there are no snoods left on the grid."""
        for row in self.grid:
            for cell in row:
                if cell is not None:
                    return False
        return True

    def _reached_danger_line(self):
        """Return True if any snood has crept past the danger line."""
        for r in range(len(self.grid)):
            for c in range(cells_in_row(r)):
                if self.grid[r][c] is None:
                    continue
                _, gy = grid_to_pixel(r, c)
                if gy + SNOOD_RADIUS >= DANGER_ROW_Y:
                    return True
        return False

    # --- Drawing ------------------------------------------------------------

    def draw(self):
        """Paint the entire screen for this frame."""
        draw_background(self.screen)

        # Side walls (purely decorative; collision uses SCREEN_WIDTH directly).
        pygame.draw.line(self.screen, WALL_COLOR, (0, 0), (0, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, WALL_COLOR,
                         (SCREEN_WIDTH - 1, 0), (SCREEN_WIDTH - 1, SCREEN_HEIGHT), 2)

        # The danger line — crossing it ends the game.
        pygame.draw.line(self.screen, DANGER_COLOR,
                         (0, DANGER_ROW_Y), (SCREEN_WIDTH, DANGER_ROW_Y), 2)

        # Draw every snood currently on the grid.
        for r in range(len(self.grid)):
            for c in range(cells_in_row(r)):
                color = self.grid[r][c]
                if color is None:
                    continue
                gx, gy = grid_to_pixel(r, c)
                draw_snood(self.screen, gx, gy, color)

        # Draw the flying snood, if there is one.
        if self.flying is not None:
            draw_snood(self.screen, self.flying['x'], self.flying['y'],
                       self.flying['color'])

        # Draw the launcher with the next-up snood loaded in.
        self._draw_launcher()

        # HUD: score in the top-left, "next" preview in the top-right.
        draw_text(self.screen, f"Score: {self.score}", 28, 10, 10, center=False)
        draw_text(self.screen, "Next:", 22, SCREEN_WIDTH - 70, 12, center=False)
        draw_snood(self.screen, SCREEN_WIDTH - 20, 22, self.next_color)

        # Game over / win banner overlays.
        if self.game_over:
            self._draw_end_banner()

        pygame.display.flip()        # Push the freshly-drawn frame to the screen.

    def _draw_launcher(self):
        """Draw the aiming line and the snood ready to be fired."""
        mx, my = pygame.mouse.get_pos()
        angle = self.aim_angle_to(mx, my)
        # Endpoint of the line: start at the launcher and walk in the aim direction.
        end_x = LAUNCHER_X + math.sin(angle) * LAUNCHER_LENGTH
        end_y = LAUNCHER_Y - math.cos(angle) * LAUNCHER_LENGTH
        pygame.draw.line(self.screen, LAUNCHER_COLOR,
                         (LAUNCHER_X, LAUNCHER_Y), (end_x, end_y), 3)
        # The current snood sits on the launcher itself.
        if self.flying is None and not self.game_over:
            draw_snood(self.screen, LAUNCHER_X, LAUNCHER_Y, self.current_color)

    def _draw_end_banner(self):
        """Show the win/lose screen with instructions to restart."""
        # A semi-transparent dark layer over the playfield, so text reads clearly.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))   # Last value is the alpha (0 = clear, 255 = solid).
        self.screen.blit(overlay, (0, 0))

        msg = "YOU WIN!" if self.win else "GAME OVER"
        draw_text(self.screen, msg, 72,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
        draw_text(self.screen, f"Final score: {self.score}", 36,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
        draw_text(self.screen, "Press R to restart, Esc to quit", 24,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)

    # --- Main loop ----------------------------------------------------------

    def run(self):
        """The classic event-loop / update / draw cycle."""
        while True:
            # 1) Handle every event since the last frame (clicks, key presses, etc.).
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_r:
                        # Restart whether or not the game is over.
                        self.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    self.fire(mx, my)

            # 2) Advance the game state.
            self.update()

            # 3) Draw the new state.
            self.draw()

            # 4) Sleep just long enough to hit our target frame rate.
            self.clock.tick(FPS)


# =============================================================================
# ENTRY POINT
# =============================================================================
# When you run `python snood.py`, Python executes the file from top to bottom.
# Everything above this point was *defining* things; the lines below actually
# *run* the game.

if __name__ == "__main__":
    SnoodGame().run()
