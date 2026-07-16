"""
===============================================================================
 SNAKE GAME - A Beginner-Friendly Pygame Implementation
===============================================================================

A classic snake game written in Python using the Pygame library.

HOW TO RUN:
    1. Install Pygame if you don't already have it:
           pip install pygame
    2. Run this file from the terminal:
           python snake_game.py

HOW TO PLAY:
    - Use the ARROW KEYS (or W/A/S/D) to steer the snake.
    - Eat the red food squares to grow longer and earn points.
    - Don't run into the walls or into your own tail!
    - Press SPACE to pause/unpause the game.
    - Press R to restart after a game over.
    - Press ESC or close the window to quit.

HOW THIS FILE IS ORGANIZED (read top-to-bottom to learn):
    1. Imports                - Bringing in the libraries we need.
    2. Constants              - All the tweakable values in one place.
    3. Helper functions       - Small reusable pieces (drawing, spawning food).
    4. Game state functions   - Starting/resetting the game.
    5. Main game loop         - The heart of the program: input -> update -> draw.

TIPS FOR EXPERIMENTING:
    - Change the constants at the top of the file to alter look & feel.
    - Try adjusting FPS to make the game faster or slower.
    - Try changing GRID_SIZE to get bigger or smaller cells.
===============================================================================
"""

# -----------------------------------------------------------------------------
# 1. IMPORTS
# -----------------------------------------------------------------------------
# "import pygame" gives us access to the Pygame library, which handles the
# window, graphics, input, and timing for us.
import pygame

# "random" is part of Python's standard library. We use it to place the food
# at random positions on the grid.
import random

# "sys" lets us cleanly exit the program using sys.exit().
import sys


# -----------------------------------------------------------------------------
# 2. CONSTANTS
# -----------------------------------------------------------------------------
# Constants are values we define once and don't change while the game runs.
# By convention in Python, constant names are written in ALL_CAPS.
# Grouping them at the top makes it EASY to tweak how the game looks and feels.

# --- Grid and window dimensions -----------------------------------------------
# The game board is a grid of square cells. The snake and food occupy one
# cell at a time. GRID_SIZE is the side length of one cell in pixels.
#
# TRY CHANGING: A larger GRID_SIZE makes the snake look chunkier and the
#               playing field smaller (fewer cells). A smaller value gives
#               you a finer grid with more room to maneuver.
GRID_SIZE = 24  # pixels per cell

# GRID_WIDTH and GRID_HEIGHT are the number of cells across and down.
#
# TRY CHANGING: Make the playfield bigger (e.g., 40 x 30) for a longer game,
#               or smaller (e.g., 15 x 15) for a more frantic experience.
GRID_WIDTH = 28   # number of columns
GRID_HEIGHT = 20  # number of rows

# The HUD (Heads-Up Display) is the strip at the top where the score appears.
# We add its height to the window so it doesn't cover the play area.
#
# TRY CHANGING: Make HUD_HEIGHT larger if you add more on-screen info later.
HUD_HEIGHT = 48  # pixels reserved at the top of the window for the score

# The actual window size in pixels is derived from the grid and HUD sizes.
# We compute these so the window always fits the grid exactly.
WINDOW_WIDTH = GRID_WIDTH * GRID_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * GRID_SIZE + HUD_HEIGHT

# --- Speed / difficulty -------------------------------------------------------
# FPS stands for "frames per second." In this game, the snake moves one cell
# per frame, so FPS also controls how fast the snake moves.
#
# TRY CHANGING: Lower (e.g., 6) for an easy, slow game.
#               Higher (e.g., 20) for a fast, twitchy challenge.
FPS = 10

# SPEED_UP_EVERY tells us how many foods the player must eat before the game
# speeds up. Set to 0 (or a very large number) to disable speeding up.
#
# TRY CHANGING: Set to 1 for a relentless difficulty curve, or 0 to keep the
#               speed constant.
SPEED_UP_EVERY = 5  # eat this many foods to trigger a speed-up

# SPEED_UP_AMOUNT is how many FPS we add each time the speed-up triggers.
SPEED_UP_AMOUNT = 1  # add this many FPS per speed-up step

# MAX_FPS caps how fast the game can ever go, so it doesn't become impossible.
MAX_FPS = 25

# --- Colors -------------------------------------------------------------------
# Colors in Pygame are (Red, Green, Blue) tuples, each from 0 to 255.
# Feel free to swap these out to reskin the game!
#
# TRY CHANGING: Pick your own palette. Pastel themes, neon themes, and
#               monochrome themes all feel very different to play.
COLOR_BACKGROUND = (18, 18, 24)      # near-black, the empty play area
COLOR_GRID_LINE = (28, 28, 36)       # subtle grid lines (set to BACKGROUND to hide)
COLOR_HUD_BG = (10, 10, 14)          # darker strip behind the score
COLOR_HUD_TEXT = (235, 235, 245)     # score text color
COLOR_SNAKE_HEAD = (120, 220, 120)   # the snake's head
COLOR_SNAKE_BODY = (70, 170, 70)     # the rest of the snake
COLOR_FOOD = (220, 80, 80)           # the food square
COLOR_OVERLAY = (0, 0, 0, 160)       # semi-transparent black for pause/game-over
COLOR_TITLE_TEXT = (255, 255, 255)   # "Game Over" / "Paused" text
COLOR_HINT_TEXT = (200, 200, 210)    # secondary instruction text

# Whether to draw the faint grid lines across the play area.
#
# TRY CHANGING: Set to False for a cleaner look.
SHOW_GRID_LINES = True

# --- Gameplay tweaks ----------------------------------------------------------
# How long the snake is when the game starts.
#
# TRY CHANGING: A longer starting length makes the early game harder.
STARTING_LENGTH = 3

# Points awarded per food eaten.
POINTS_PER_FOOD = 10

# If WRAP_AROUND is True, the snake passes through walls and appears on the
# other side instead of dying. Great for a more forgiving game.
#
# TRY CHANGING: Flip to True for the "Nokia phone" style where walls don't
#               kill you — only hitting yourself does.
WRAP_AROUND = False

# --- Text / fonts -------------------------------------------------------------
# The name of the window as it appears in your OS title bar.
WINDOW_TITLE = "Snake"

# Font sizes for different on-screen text elements.
FONT_SIZE_HUD = 24
FONT_SIZE_TITLE = 64
FONT_SIZE_HINT = 22


# -----------------------------------------------------------------------------
# 3. DIRECTION CONSTANTS
# -----------------------------------------------------------------------------
# We represent directions as (dx, dy) pairs — the change in column (x) and
# row (y) per step. For example, moving right means x increases by 1 and y
# stays the same, so RIGHT = (1, 0). Using tuples makes "move one step" as
# simple as adding the direction to the current position.
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


# -----------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
# Breaking the code into small functions with descriptive names makes it
# easier to read and to change one thing at a time without breaking others.

def grid_to_pixel(cell):
    """Convert a (column, row) grid cell into (x, y) pixel coordinates.

    The play area sits BELOW the HUD, so we shift the y-pixel down by
    HUD_HEIGHT. This keeps the drawing code simple elsewhere.
    """
    col, row = cell
    x = col * GRID_SIZE
    y = row * GRID_SIZE + HUD_HEIGHT
    return x, y


def draw_cell(surface, cell, color, inset=2):
    """Draw a single filled square at a grid cell.

    `inset` leaves a small gap around each cell so the snake segments and
    food don't visually merge into one big blob. Lower the inset for a
    chunkier look, raise it for a more "pixel-art" spaced-out look.
    """
    x, y = grid_to_pixel(cell)
    # pygame.Rect represents a rectangle: (left, top, width, height).
    rect = pygame.Rect(
        x + inset,
        y + inset,
        GRID_SIZE - inset * 2,
        GRID_SIZE - inset * 2,
    )
    pygame.draw.rect(surface, color, rect)


def draw_grid_lines(surface):
    """Draw faint lines between cells so the grid is visible."""
    # Vertical lines — one between every pair of columns.
    for col in range(GRID_WIDTH + 1):
        x = col * GRID_SIZE
        pygame.draw.line(
            surface,
            COLOR_GRID_LINE,
            (x, HUD_HEIGHT),
            (x, WINDOW_HEIGHT),
        )
    # Horizontal lines — one between every pair of rows.
    for row in range(GRID_HEIGHT + 1):
        y = row * GRID_SIZE + HUD_HEIGHT
        pygame.draw.line(
            surface,
            COLOR_GRID_LINE,
            (0, y),
            (WINDOW_WIDTH, y),
        )


def spawn_food(snake_cells):
    """Choose a random empty grid cell for the next piece of food.

    We must not place food on top of the snake, so we keep picking random
    cells until we find one the snake doesn't occupy. For normal grid sizes
    this is nearly instantaneous.
    """
    # Build the set of cells currently occupied by the snake. Using a set
    # makes the "is this cell free?" check very fast.
    occupied = set(snake_cells)
    while True:
        candidate = (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1),
        )
        if candidate not in occupied:
            return candidate


def draw_hud(surface, font, score, high_score, paused):
    """Draw the score strip across the top of the window."""
    # Fill the HUD area with its background color.
    hud_rect = pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT)
    pygame.draw.rect(surface, COLOR_HUD_BG, hud_rect)

    # Build the text we want to show.
    left_text = f"Score: {score}"
    right_text = f"Best: {high_score}"
    if paused:
        right_text = "PAUSED  —  " + right_text

    # Render the text onto small surfaces. "True" enables anti-aliasing,
    # which makes text edges look smooth instead of blocky.
    left_surface = font.render(left_text, True, COLOR_HUD_TEXT)
    right_surface = font.render(right_text, True, COLOR_HUD_TEXT)

    # Vertically center the text within the HUD strip.
    left_y = (HUD_HEIGHT - left_surface.get_height()) // 2
    right_y = (HUD_HEIGHT - right_surface.get_height()) // 2

    # Blit ("block image transfer") the text onto the main surface.
    surface.blit(left_surface, (16, left_y))
    surface.blit(right_surface, (WINDOW_WIDTH - right_surface.get_width() - 16, right_y))


def draw_overlay(surface, title_font, hint_font, title_text, hint_text):
    """Dim the screen and show a big title plus a small hint underneath.

    Used for both the "Paused" and "Game Over" screens.
    """
    # To draw a SEMI-TRANSPARENT overlay, we create a separate surface with
    # per-pixel alpha (SRCALPHA), fill it with our overlay color (which has
    # an alpha value), and then blit it on top of everything else.
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(COLOR_OVERLAY)
    surface.blit(overlay, (0, 0))

    # Render the two pieces of text.
    title_surface = title_font.render(title_text, True, COLOR_TITLE_TEXT)
    hint_surface = hint_font.render(hint_text, True, COLOR_HINT_TEXT)

    # Center the title roughly in the middle of the window.
    title_x = (WINDOW_WIDTH - title_surface.get_width()) // 2
    title_y = (WINDOW_HEIGHT - title_surface.get_height()) // 2 - 20

    # Put the hint just below the title.
    hint_x = (WINDOW_WIDTH - hint_surface.get_width()) // 2
    hint_y = title_y + title_surface.get_height() + 10

    surface.blit(title_surface, (title_x, title_y))
    surface.blit(hint_surface, (hint_x, hint_y))


# -----------------------------------------------------------------------------
# 5. GAME STATE HELPERS
# -----------------------------------------------------------------------------

def create_initial_snake():
    """Build the starting snake as a list of (column, row) cells.

    The HEAD is always the FIRST element of the list (index 0). The tail is
    the LAST element. Representing the snake this way makes movement easy:
    we add a new head at the front and (usually) drop the last tail cell.
    """
    # Start the snake horizontally centered, facing right.
    center_col = GRID_WIDTH // 2
    center_row = GRID_HEIGHT // 2

    # Build the body from head -> tail. The head is at the highest column
    # so that moving RIGHT is the natural first direction.
    snake = []
    for i in range(STARTING_LENGTH):
        snake.append((center_col - i, center_row))
    return snake


def reset_game():
    """Return a fresh "game state" dictionary for a new round.

    Keeping all mutable state in one dictionary (instead of many global
    variables) makes it trivial to reset: we just build a new dictionary.
    """
    snake = create_initial_snake()
    return {
        "snake": snake,                    # list of (col, row) cells, head first
        "direction": RIGHT,                # current movement direction
        "pending_direction": RIGHT,        # the next direction to apply (set by input)
        "food": spawn_food(snake),         # (col, row) of the current food
        "score": 0,                        # player's score this round
        "foods_eaten": 0,                  # used to trigger speed-ups
        "fps": FPS,                        # current speed; may rise over time
        "alive": True,                     # False once the snake dies
        "paused": False,                   # True while the player has paused
    }


# -----------------------------------------------------------------------------
# 6. MAIN GAME LOOP
# -----------------------------------------------------------------------------
# Every Pygame game boils down to this loop:
#     1. Handle events (keyboard, window close, etc.)
#     2. Update the game state (move the snake, check collisions)
#     3. Draw everything to the screen
#     4. Wait just long enough to hit the target frame rate
# Then repeat until the player quits.

def main():
    # pygame.init() starts up all of Pygame's subsystems (video, fonts, etc.).
    pygame.init()

    # Create the window. The returned object is the "surface" we draw onto.
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # A Clock is used to control the frame rate so the game doesn't run as
    # fast as the CPU can manage (which would be WAY too fast).
    clock = pygame.time.Clock()

    # Using None for the font name asks Pygame for the default system font,
    # so we don't need any external font files.
    hud_font = pygame.font.SysFont(None, FONT_SIZE_HUD)
    title_font = pygame.font.SysFont(None, FONT_SIZE_TITLE)
    hint_font = pygame.font.SysFont(None, FONT_SIZE_HINT)

    # The game state holds everything that changes between frames.
    state = reset_game()

    # Remember the best score across restarts within the same session.
    high_score = 0

    # --- THE MAIN LOOP --------------------------------------------------------
    running = True
    while running:

        # -----------------------------------------------------------------
        # STEP 1: HANDLE INPUT AND OS EVENTS
        # -----------------------------------------------------------------
        # pygame.event.get() returns every event that has happened since
        # the last call (key presses, window-close clicks, mouse moves, ...).
        for event in pygame.event.get():
            # The user closed the window.
            if event.type == pygame.QUIT:
                running = False

            # A key was just pressed down.
            elif event.type == pygame.KEYDOWN:
                # ESC always quits.
                if event.key == pygame.K_ESCAPE:
                    running = False

                # R restarts the game — useful after game over OR mid-game.
                elif event.key == pygame.K_r:
                    state = reset_game()

                # SPACE toggles pause, but only while the snake is alive.
                elif event.key == pygame.K_SPACE and state["alive"]:
                    state["paused"] = not state["paused"]

                # Arrow keys / WASD change direction.
                #
                # We store the new direction in "pending_direction" and apply
                # it on the next move. This prevents a classic bug where the
                # player presses two keys quickly (e.g., UP then LEFT while
                # moving RIGHT) and the snake reverses into itself within
                # one frame.
                elif event.key in (pygame.K_UP, pygame.K_w):
                    # Don't allow an immediate 180° turn into your own neck.
                    if state["direction"] != DOWN:
                        state["pending_direction"] = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if state["direction"] != UP:
                        state["pending_direction"] = DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if state["direction"] != RIGHT:
                        state["pending_direction"] = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if state["direction"] != LEFT:
                        state["pending_direction"] = RIGHT

        # -----------------------------------------------------------------
        # STEP 2: UPDATE GAME STATE
        # -----------------------------------------------------------------
        # We only move the snake if the game is actively running — not
        # while paused, and not after a game over.
        if state["alive"] and not state["paused"]:

            # Lock in the direction the player requested since last tick.
            state["direction"] = state["pending_direction"]

            # Compute where the new head will be by adding the direction
            # vector to the current head position.
            head_col, head_row = state["snake"][0]
            d_col, d_row = state["direction"]
            new_head = (head_col + d_col, head_row + d_row)

            # Handle walls: either wrap around or die, depending on config.
            if WRAP_AROUND:
                # The "% GRID_WIDTH" trick makes -1 become GRID_WIDTH - 1
                # and GRID_WIDTH become 0, seamlessly wrapping the edges.
                new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
            else:
                # Check if the new head is outside the play area.
                off_horiz = new_head[0] < 0 or new_head[0] >= GRID_WIDTH
                off_vert = new_head[1] < 0 or new_head[1] >= GRID_HEIGHT
                if off_horiz or off_vert:
                    state["alive"] = False

            # Only continue updating if we haven't just died hitting a wall.
            if state["alive"]:

                # Did we eat food this step?
                ate_food = new_head == state["food"]

                # Self-collision check.
                # The tail cell will move out of the way this step UNLESS we
                # just ate food (in which case the snake grows). So the set
                # of "blocking" cells is the whole snake if we ate, or
                # everything except the tail cell if we didn't.
                if ate_food:
                    body_to_check = state["snake"]
                else:
                    body_to_check = state["snake"][:-1]

                if new_head in body_to_check:
                    state["alive"] = False

            # Update the snake list if we're still alive.
            if state["alive"]:
                # Add the new head to the FRONT of the list.
                state["snake"].insert(0, new_head)

                if ate_food:
                    # Grow: keep the tail in place (don't pop it).
                    state["score"] += POINTS_PER_FOOD
                    state["foods_eaten"] += 1
                    state["food"] = spawn_food(state["snake"])

                    # Optional speed-up every N foods.
                    if (
                        SPEED_UP_EVERY > 0
                        and state["foods_eaten"] % SPEED_UP_EVERY == 0
                        and state["fps"] < MAX_FPS
                    ):
                        state["fps"] = min(MAX_FPS, state["fps"] + SPEED_UP_AMOUNT)
                else:
                    # Normal move: pop the tail so length stays the same.
                    state["snake"].pop()

            # Update high score if the current score is better.
            if state["score"] > high_score:
                high_score = state["score"]

        # -----------------------------------------------------------------
        # STEP 3: DRAW EVERYTHING
        # -----------------------------------------------------------------
        # Paint the play-area background first.
        screen.fill(COLOR_BACKGROUND)

        # Faint grid lines, if enabled.
        if SHOW_GRID_LINES:
            draw_grid_lines(screen)

        # The food.
        draw_cell(screen, state["food"], COLOR_FOOD)

        # The snake — head a brighter color so you can see which way you're
        # pointing at a glance.
        for index, segment in enumerate(state["snake"]):
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            draw_cell(screen, segment, color)

        # HUD on top.
        draw_hud(screen, hud_font, state["score"], high_score, state["paused"])

        # Pause/game-over overlays sit on top of the whole screen.
        if not state["alive"]:
            draw_overlay(
                screen,
                title_font,
                hint_font,
                title_text="Game Over",
                hint_text="Press R to play again, ESC to quit",
            )
        elif state["paused"]:
            draw_overlay(
                screen,
                title_font,
                hint_font,
                title_text="Paused",
                hint_text="Press SPACE to resume",
            )

        # pygame.display.flip() pushes everything we've drawn to the actual
        # window. Until this is called, drawing only happens in memory.
        pygame.display.flip()

        # -----------------------------------------------------------------
        # STEP 4: CAP THE FRAME RATE
        # -----------------------------------------------------------------
        # clock.tick(fps) sleeps just long enough that we don't exceed the
        # target FPS. It's how we keep the snake from moving at light speed
        # on fast computers.
        clock.tick(state["fps"])

    # Outside the loop now: the player asked to quit.
    pygame.quit()
    sys.exit()


# -----------------------------------------------------------------------------
# 7. ENTRY POINT
# -----------------------------------------------------------------------------
# This idiom means "only call main() if this file is being RUN directly,
# not if it's being imported from another Python file." It's the standard
# Python way to mark your program's entry point.
if __name__ == "__main__":
    main()
