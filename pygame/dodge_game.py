"""
============================================================
  GRID DODGE  --  a tiny arcade game written in Pygame
============================================================

How to play:
  - You are the dot in the middle of a 3x3 grid.
  - Hold an arrow key (or W/A/S/D) to LEAN toward that side.
  - Hold two keys at once to lean into a CORNER.
       Example: UP + RIGHT  ->  top-right corner.
  - Release all keys and you snap back to the center.
  - Blocks fly in from the four sides. Don't be in their cell
    when they pass through you!
  - The longer you survive, the faster the blocks come.
  - When you die, press SPACE to start a new game.

This file is meant to be read as well as run. Almost every
section has comments explaining WHAT is happening and WHY.
Look for the big "TWEAK ME" constants at the top -- changing
their numbers is a great way to learn how the game works.
"""

# ------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------
# `pygame` is the library that gives us a window, drawing
# functions, keyboard input, and a clock for timing.
# `random` lets us pick blocks to spawn unpredictably.
# `sys` is used so we can cleanly quit the program.
import pygame
import random
import sys


# ============================================================
# 2. CONSTANTS  --  "TWEAK ME" knobs for the whole game
# ============================================================
# Constants are values that never change while the game runs.
# Putting them all up here means you can experiment by
# changing one number and immediately seeing the effect,
# without hunting through the whole file.

# ---- Window / grid ----
# The grid is always 3 cells wide and 3 cells tall.
# CELL_SIZE controls how big each cell is in pixels, and the
# rest of the layout is computed from it. Try 100 or 200!
CELL_SIZE      = 140       # pixel size of one grid cell
GRID_COLS      = 3         # don't change unless you also rewrite the movement logic
GRID_ROWS      = 3         # (the game's "lean" idea assumes 3x3)
GRID_MARGIN    = 60        # space around the grid inside the window
HUD_HEIGHT     = 80        # space at the top for score / messages

# Total window size is derived from the grid. We don't hard-
# code the window size so changing CELL_SIZE just works.
WINDOW_WIDTH   = GRID_MARGIN * 2 + CELL_SIZE * GRID_COLS
WINDOW_HEIGHT  = GRID_MARGIN * 2 + CELL_SIZE * GRID_ROWS + HUD_HEIGHT

# ---- Colors (R, G, B) ----
# Each value goes from 0 (none) to 255 (max). Change these
# to re-skin the game. e.g. swap BG_COLOR for (20, 20, 40)
# to get a moody dark-blue background.
BG_COLOR        = (18, 18, 24)      # background
GRID_COLOR      = (45, 45, 60)      # grid cell outlines
CENTER_COLOR    = (30, 30, 45)      # subtle highlight on center cell
PLAYER_COLOR    = (90, 220, 255)    # the player dot
PLAYER_OUTLINE  = (220, 250, 255)
BLOCK_COLOR     = (255, 90, 110)    # incoming danger blocks
TEXT_COLOR      = (235, 235, 245)
DIM_TEXT_COLOR  = (140, 140, 160)
GAMEOVER_COLOR  = (255, 200, 100)

# ---- Player ----
# How big the player dot is, and how quickly it slides between
# cells. SNAP_SPEED is "fraction of remaining distance per
# frame". Higher = snappier. Try values from 0.1 to 0.5.
PLAYER_RADIUS   = 22
SNAP_SPEED      = 0.25

# ---- Blocks ----
# Blocks are squares that fly across the grid in straight
# lines (horizontally or vertically). They occupy one row or
# column at a time and move from one edge to the other.
BLOCK_SIZE_RATIO = 0.85   # how big a block is vs. a cell (1.0 = fills cell)

# Blocks start slow and speed up over time. Speed is measured
# in "cells per second" -- so 2.0 means it crosses two grid
# cells every second.
START_BLOCK_SPEED = 2.0
MAX_BLOCK_SPEED   = 9.0
# How many "speed units per second" to add. Smaller = gentler
# difficulty curve; bigger = panic faster. Try 0.05 vs 0.4.
SPEED_RAMP        = 0.15

# How often new blocks appear (in seconds between spawns).
# This also gets shorter over time so the screen fills up.
START_SPAWN_GAP   = 1.10
MIN_SPAWN_GAP     = 0.28
SPAWN_GAP_RAMP    = 0.015  # how much to shave off per second of survival

# Chance that a "spawn event" actually fires TWO blocks at
# once instead of one. 0.0 = never, 1.0 = always. The game
# will refuse to spawn a pair that traps the player, so the
# real rate of doubles is a bit lower than this number.
DOUBLE_BLOCK_CHANCE = 0.35

# ---- Misc ----
FPS              = 60       # how many times per second we redraw
SCORE_PER_SECOND = 10       # points awarded for staying alive


# ============================================================
# 3. KEY MAPPING  --  which keyboard keys count as which lean?
# ============================================================
# We support BOTH arrow keys and WASD. For each direction we
# keep a list of accepted key codes. Pygame gives us constants
# like pygame.K_UP and pygame.K_w that represent these keys.
KEYS_UP    = (pygame.K_UP,    pygame.K_w)
KEYS_DOWN  = (pygame.K_DOWN,  pygame.K_s)
KEYS_LEFT  = (pygame.K_LEFT,  pygame.K_a)
KEYS_RIGHT = (pygame.K_RIGHT, pygame.K_d)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def cell_to_pixel(col, row):
    """
    Convert a grid coordinate (col, row) where col and row are
    each 0, 1, or 2 into the pixel position of the CENTER of
    that cell on the screen.

    We use this every time we draw something at a grid cell.
    """
    x = GRID_MARGIN + col * CELL_SIZE + CELL_SIZE // 2
    y = HUD_HEIGHT + GRID_MARGIN + row * CELL_SIZE + CELL_SIZE // 2
    return (x, y)


def any_key_pressed(keys_state, key_list):
    """
    Returns True if ANY key in `key_list` is currently held.

    `keys_state` comes from pygame.key.get_pressed(), which
    is basically a big array we can index by key code.
    """
    return any(keys_state[k] for k in key_list)


def get_target_cell(keys_state):
    """
    Look at which keys are held right now and decide which
    grid cell the player wants to be in.

    Default is the center (1, 1). Holding LEFT pulls col to 0,
    RIGHT pulls it to 2, UP pulls row to 0, DOWN pulls it to 2.
    Holding LEFT and RIGHT at the same time cancels out (and
    same for UP/DOWN), which feels natural.
    """
    col = 1   # 0 = left column, 1 = middle, 2 = right
    row = 1   # 0 = top row,    1 = middle, 2 = bottom

    left  = any_key_pressed(keys_state, KEYS_LEFT)
    right = any_key_pressed(keys_state, KEYS_RIGHT)
    up    = any_key_pressed(keys_state, KEYS_UP)
    down  = any_key_pressed(keys_state, KEYS_DOWN)

    # Opposing keys cancel. Only commit to a side if exactly
    # one of the pair is pressed.
    if left and not right:
        col = 0
    elif right and not left:
        col = 2

    if up and not down:
        row = 0
    elif down and not up:
        row = 2

    return (col, row)


# ============================================================
# 5. THE BLOCK CLASS
# ============================================================
# A "class" is a blueprint for an object that bundles data
# (its position, direction, speed) with behavior (update,
# draw). We make a new Block whenever one spawns.
class Block:
    """
    A danger block that travels along ONE row or ONE column
    of the grid, from one edge to the other.

    `axis` tells us which way it travels:
        "h" (horizontal) -- moves along a row
        "v" (vertical)   -- moves along a column

    `lane` is the row index (if axis == "h") or column index
    (if axis == "v") it lives in.

    `direction` is +1 (left->right or top->bottom) or -1.
    """

    def __init__(self, axis, lane, direction, speed):
        self.axis = axis
        self.lane = lane
        self.direction = direction
        self.speed = speed   # in "cells per second"

        # `progress` is the block's position along its lane,
        # measured in cells. We start it just OFF the visible
        # grid so the block slides in from outside the edge.
        # If moving in +1 direction, start at -1 (one cell
        # before the grid). If -1, start at GRID_COLS (one
        # cell past the right edge).
        if direction > 0:
            self.progress = -1.0
        else:
            self.progress = float(GRID_COLS if axis == "h" else GRID_ROWS)

    def update(self, dt):
        """
        Advance the block by one frame. `dt` is the time since
        the last frame in seconds. Multiplying speed by dt
        makes movement smooth even if the framerate hiccups.
        """
        self.progress += self.direction * self.speed * dt

    def is_off_screen(self):
        """
        Once the block has fully passed the far edge, it's
        gone forever and the main loop will throw it away.
        """
        if self.direction > 0:
            return self.progress > (GRID_COLS if self.axis == "h" else GRID_ROWS) + 0.5
        else:
            return self.progress < -1.5

    def occupied_cell(self):
        """
        Which grid cell (col, row) is the block CURRENTLY
        sitting in? We round `progress` to the nearest whole
        cell. If it's outside 0..2 we return None (meaning:
        not yet on the grid, or already past it).

        This is what the collision check uses.
        """
        nearest = round(self.progress)
        if self.axis == "h":
            if 0 <= nearest <= GRID_COLS - 1:
                return (nearest, self.lane)
        else:
            if 0 <= nearest <= GRID_ROWS - 1:
                return (self.lane, nearest)
        return None

    def will_pass_through(self, col, row):
        """
        Will this block, at some point during its trip, pass
        through cell (col, row)? Used to decide whether
        spawning this block could trap the player.
        """
        if self.axis == "h":
            return row == self.lane
        else:
            return col == self.lane

    def pixel_position(self):
        """
        Convert the block's current `progress` into pixel
        coordinates so we can draw it. We allow non-integer
        progress so the block looks like it's smoothly
        sliding across, not teleporting cell-to-cell.
        """
        if self.axis == "h":
            # progress is a fractional column index
            x = GRID_MARGIN + self.progress * CELL_SIZE + CELL_SIZE // 2
            y = HUD_HEIGHT + GRID_MARGIN + self.lane * CELL_SIZE + CELL_SIZE // 2
        else:
            x = GRID_MARGIN + self.lane * CELL_SIZE + CELL_SIZE // 2
            y = HUD_HEIGHT + GRID_MARGIN + self.progress * CELL_SIZE + CELL_SIZE // 2
        return (x, y)


# ============================================================
# 6. SPAWN LOGIC  --  picking blocks that don't trap the player
# ============================================================
# This is the trickiest piece. The brief says the player must
# ALWAYS have a way to avoid the blocks. So before we add a
# new block (or pair of blocks) to the game, we check that at
# least one of the 9 grid cells is still "safe": no existing
# block AND no incoming block will pass through it during the
# upcoming dangerous moment.
#
# We treat a cell as "threatened" if any current-or-proposed
# block will travel through it. The player must have at least
# one cell that is NOT threatened, otherwise they'd be doomed.

def threatened_cells(blocks):
    """Set of cells that some block will pass through."""
    threatened = set()
    for b in blocks:
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                if b.will_pass_through(c, r):
                    threatened.add((c, r))
    return threatened


def has_safe_cell(blocks):
    """True if at least one of the 9 cells is not threatened."""
    threatened = threatened_cells(blocks)
    total_cells = GRID_COLS * GRID_ROWS
    return len(threatened) < total_cells


def make_random_block(speed):
    """Create a single block with a random axis, lane, and direction."""
    axis = random.choice(("h", "v"))
    if axis == "h":
        lane = random.randrange(GRID_ROWS)
    else:
        lane = random.randrange(GRID_COLS)
    direction = random.choice((-1, 1))
    return Block(axis, lane, direction, speed)


def try_spawn_blocks(existing_blocks, speed, want_double):
    """
    Try to create one (or two, if want_double) new blocks
    such that the player still has at least one safe cell
    after they're added.

    We retry a few times. If every attempt would trap the
    player, we give up and return an empty list -- the game
    will simply not spawn this round. This keeps the
    promise: there's always a way out.
    """
    attempts = 20
    for _ in range(attempts):
        candidates = [make_random_block(speed)]
        if want_double:
            candidates.append(make_random_block(speed))

        # Don't allow two blocks that share the exact same
        # axis+lane+direction (they'd just stack on top of
        # each other, which looks weird).
        if want_double:
            a, b = candidates
            if a.axis == b.axis and a.lane == b.lane and a.direction == b.direction:
                continue

        if has_safe_cell(existing_blocks + candidates):
            return candidates

    return []   # couldn't find a fair spawn this time


# ============================================================
# 7. THE GAME ITSELF
# ============================================================
def run_game():
    """
    One full session: shows the title, plays until the player
    dies, shows the game-over screen, and waits for SPACE to
    play again. Returns when the player closes the window.
    """
    # ---- Pygame setup ----
    # pygame.init() turns on all of pygame's subsystems
    # (graphics, fonts, etc). Always call it once at start.
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Grid Dodge")
    clock = pygame.time.Clock()

    # Fonts: one big, one small. Use the default system font
    # so we don't depend on any particular font being installed.
    big_font   = pygame.font.SysFont(None, 64)
    mid_font   = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)

    # We loop forever. Inside the loop we play one round at a
    # time. The OUTER loop is "play repeatedly", the INNER
    # loops handle one round each.
    while True:
        # --------------------------------------------------
        # ROUND SETUP  --  reset everything for a new game
        # --------------------------------------------------
        blocks = []                         # all live blocks
        elapsed = 0.0                       # seconds survived
        time_to_next_spawn = START_SPAWN_GAP
        block_speed = START_BLOCK_SPEED
        spawn_gap   = START_SPAWN_GAP

        # The player is described by the cell they're trying
        # to be in (target) and their current pixel position
        # (which slides toward the target each frame).
        player_target_cell = (1, 1)
        player_pixel = list(cell_to_pixel(1, 1))

        game_over = False
        final_score = 0

        # --------------------------------------------------
        # INNER LOOP  --  one frame of one round
        # --------------------------------------------------
        while not game_over:
            # `dt` is "delta time": how long the previous
            # frame took, in seconds. tick(FPS) tries to cap
            # us at FPS frames per second AND tells us how
            # long it actually waited.
            dt = clock.tick(FPS) / 1000.0

            # ---- Handle window/system events ----
            # `events` are one-shot things like key presses,
            # mouse clicks, or the user clicking the X button.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # ---- Read held keys for movement ----
            # Unlike events, this tells us what's held RIGHT
            # NOW, which is what we want for "lean" movement.
            keys_state = pygame.key.get_pressed()
            player_target_cell = get_target_cell(keys_state)

            # ---- Move the player smoothly toward target ----
            # We don't teleport -- we move a fraction of the
            # remaining distance each frame. This is called
            # "easing" and feels much nicer than a jump.
            target_pixel = cell_to_pixel(*player_target_cell)
            player_pixel[0] += (target_pixel[0] - player_pixel[0]) * SNAP_SPEED
            player_pixel[1] += (target_pixel[1] - player_pixel[1]) * SNAP_SPEED

            # ---- Difficulty ramp ----
            # Survive longer -> faster blocks, more often.
            elapsed += dt
            block_speed = min(MAX_BLOCK_SPEED,
                              START_BLOCK_SPEED + SPEED_RAMP * elapsed)
            spawn_gap = max(MIN_SPAWN_GAP,
                            START_SPAWN_GAP - SPAWN_GAP_RAMP * elapsed)

            # ---- Spawn new blocks on a timer ----
            time_to_next_spawn -= dt
            if time_to_next_spawn <= 0:
                want_double = random.random() < DOUBLE_BLOCK_CHANCE
                new_blocks = try_spawn_blocks(blocks, block_speed, want_double)
                blocks.extend(new_blocks)
                time_to_next_spawn = spawn_gap

            # ---- Update each block, drop ones that left ----
            # We build a fresh list of "still on screen"
            # blocks. This is simpler than removing items
            # from a list while iterating it.
            still_alive = []
            for b in blocks:
                b.update(dt)
                if not b.is_off_screen():
                    still_alive.append(b)
            blocks = still_alive

            # ---- Collision check ----
            # The player counts as "in" their TARGET cell.
            # That is: as long as you're holding the right
            # combination of keys when the block crosses your
            # cell, you live, even if you haven't finished
            # sliding visually. This feels fair to the player.
            for b in blocks:
                if b.occupied_cell() == player_target_cell:
                    game_over = True
                    final_score = int(elapsed * SCORE_PER_SECOND)
                    break

            # ==========================================
            # DRAWING -- everything below paints to the screen
            # ==========================================
            # Order matters: things drawn LATER appear ON TOP.
            # So: background -> grid -> blocks -> player -> HUD.

            screen.fill(BG_COLOR)

            # Subtle highlight on the center cell so the
            # "rest position" is visible.
            cx, cy = cell_to_pixel(1, 1)
            highlight_rect = pygame.Rect(0, 0, CELL_SIZE - 6, CELL_SIZE - 6)
            highlight_rect.center = (cx, cy)
            pygame.draw.rect(screen, CENTER_COLOR, highlight_rect, border_radius=8)

            # Grid cell outlines
            for c in range(GRID_COLS):
                for r in range(GRID_ROWS):
                    px, py = cell_to_pixel(c, r)
                    rect = pygame.Rect(0, 0, CELL_SIZE - 4, CELL_SIZE - 4)
                    rect.center = (px, py)
                    pygame.draw.rect(screen, GRID_COLOR, rect, width=2,
                                     border_radius=8)

            # Blocks
            block_pixel_size = int(CELL_SIZE * BLOCK_SIZE_RATIO)
            for b in blocks:
                bx, by = b.pixel_position()
                rect = pygame.Rect(0, 0, block_pixel_size, block_pixel_size)
                rect.center = (bx, by)
                pygame.draw.rect(screen, BLOCK_COLOR, rect, border_radius=6)

            # Player (drawn last so it's always visible)
            pygame.draw.circle(screen, PLAYER_OUTLINE,
                               (int(player_pixel[0]), int(player_pixel[1])),
                               PLAYER_RADIUS + 3)
            pygame.draw.circle(screen, PLAYER_COLOR,
                               (int(player_pixel[0]), int(player_pixel[1])),
                               PLAYER_RADIUS)

            # HUD: time survived + speed
            score_now = int(elapsed * SCORE_PER_SECOND)
            score_surf = mid_font.render(f"Score: {score_now}",
                                         True, TEXT_COLOR)
            screen.blit(score_surf, (GRID_MARGIN, 18))

            speed_surf = small_font.render(
                f"Speed x{block_speed:.1f}", True, DIM_TEXT_COLOR)
            screen.blit(speed_surf,
                        (WINDOW_WIDTH - GRID_MARGIN - speed_surf.get_width(), 28))

            # Hint at the very bottom of the screen
            hint = small_font.render(
                "Arrows / WASD to lean.  Release = center.",
                True, DIM_TEXT_COLOR)
            screen.blit(hint,
                        (WINDOW_WIDTH // 2 - hint.get_width() // 2,
                         WINDOW_HEIGHT - 30))

            # `flip` shows everything we just drew. Without
            # this call the window stays blank!
            pygame.display.flip()

        # ------------------------------------------------------
        # GAME OVER SCREEN  --  wait for SPACE or window close
        # ------------------------------------------------------
        waiting = True
        while waiting:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False  # break out -> outer loop restarts a round

            # Dim the screen a bit so the message stands out.
            # We draw a semi-transparent dark rectangle over
            # whatever was last on screen.
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(170)        # 0 = invisible, 255 = solid
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            title = big_font.render("GAME OVER", True, GAMEOVER_COLOR)
            score = mid_font.render(f"Final Score: {final_score}",
                                    True, TEXT_COLOR)
            prompt = small_font.render(
                "Press SPACE to play again, or close the window to quit.",
                True, DIM_TEXT_COLOR)

            screen.blit(title,
                        (WINDOW_WIDTH // 2 - title.get_width() // 2,
                         WINDOW_HEIGHT // 2 - 80))
            screen.blit(score,
                        (WINDOW_WIDTH // 2 - score.get_width() // 2,
                         WINDOW_HEIGHT // 2 - 10))
            screen.blit(prompt,
                        (WINDOW_WIDTH // 2 - prompt.get_width() // 2,
                         WINDOW_HEIGHT // 2 + 40))

            pygame.display.flip()


# ============================================================
# 8. ENTRY POINT
# ============================================================
# This `if __name__ == "__main__":` line is a Python idiom.
# It means: "only run the game if this file is executed
# directly (not imported by another script)." It's optional
# for a tiny script like this, but it's a great habit.
if __name__ == "__main__":
    run_game()
