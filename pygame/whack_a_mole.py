"""
=============================================================================
                    WHACK-A-MOLE - A Beginner's Pygame Project
=============================================================================

Welcome! This is a simple Whack-a-Mole game built with Python and Pygame.
It's designed as a TEACHING EXAMPLE, so you'll find lots of comments
explaining what each piece of code does and why.

HOW TO PLAY:
  - Moles will pop up randomly out of holes
  - Click on them with your mouse to "whack" them and earn points
  - You have a limited time to score as many hits as you can!
  - Press R to restart after the game ends

HOW TO RUN:
  1. Make sure Python is installed (https://www.python.org)
  2. Install Pygame by typing in your terminal:  pip install pygame
  3. Run this file:  python whack_a_mole.py

WHAT YOU CAN LEARN HERE:
  - The "game loop" pattern (the heart of every game)
  - Handling user input (mouse clicks, keyboard)
  - Drawing shapes and text on the screen
  - Using timers and randomness
  - Organizing code with classes and functions
  - Constants vs variables

EXPERIMENT! Look for the "TRY CHANGING" hints throughout the constants section.
Tweaking values is one of the best ways to learn how a program works.
=============================================================================
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
# "import" statements bring in code that someone else has written so we don't
# have to build everything from scratch.

import pygame  # The game library we're using - handles graphics, sound, input
import random  # For randomly choosing which hole the mole pops out of
import sys     # Lets us cleanly exit the program when the user closes the window


# =============================================================================
# CONSTANTS - Values that don't change while the game is running
# =============================================================================
# By convention in Python, CONSTANTS are written in ALL_CAPS_WITH_UNDERSCORES.
# Putting them all at the top makes it easy to tweak the game without hunting
# through hundreds of lines of code.
#
# TRY CHANGING these values to see how the game changes!
# -----------------------------------------------------------------------------

# --- Window settings ---
WINDOW_WIDTH = 800        # How wide the game window is, in pixels
WINDOW_HEIGHT = 600       # How tall the game window is, in pixels
WINDOW_TITLE = "Whack-a-Mole!"  # The text shown in the window's title bar
FPS = 60                  # Frames per second. Higher = smoother. TRY: 30 or 120

# --- Colors (Red, Green, Blue values from 0 to 255) ---
# Computers describe colors as a mix of Red, Green, and Blue light.
# (0, 0, 0) is black (no light), (255, 255, 255) is white (all colors mixed).
# TRY CHANGING these to give the game a different mood!
COLOR_BACKGROUND = (135, 206, 235)   # Sky blue
COLOR_GRASS = (76, 175, 80)          # Green grass at the bottom
COLOR_HOLE_DARK = (60, 40, 20)       # Dark brown hole interior
COLOR_HOLE_RIM = (101, 67, 33)       # Lighter brown for the hole edge
COLOR_MOLE_BODY = (139, 90, 43)      # Brown mole body
COLOR_MOLE_BELLY = (210, 180, 140)   # Tan belly
COLOR_MOLE_NOSE = (50, 30, 20)       # Dark brown nose
COLOR_TEXT = (255, 255, 255)         # White text
COLOR_TEXT_SHADOW = (0, 0, 0)        # Black shadow behind text for readability
COLOR_HIT_FLASH = (255, 215, 0)      # Gold flash when you hit a mole

# --- Game grid: where the holes go ---
# We arrange holes in a grid, like a tic-tac-toe board.
GRID_ROWS = 3             # Number of rows of holes. TRY: 2 or 4
GRID_COLS = 4             # Number of columns. TRY: 3 or 5
HOLE_RADIUS = 50          # How big each hole is. TRY: 30 (smaller, harder!) or 70

# --- Mole appearance ---
MOLE_RADIUS = 40          # How big the mole's head is. Smaller = harder to hit
MOLE_RISE_HEIGHT = 60     # How far the mole pops up out of the hole

# --- Game timing (in MILLISECONDS - 1000 ms = 1 second) ---
GAME_DURATION_MS = 30000          # How long a round lasts. TRY: 60000 for 1 minute
MOLE_VISIBLE_TIME_MIN = 600       # Shortest time a mole stays up (faster = harder)
MOLE_VISIBLE_TIME_MAX = 1500      # Longest time a mole stays up
MOLE_SPAWN_DELAY_MIN = 200        # Shortest wait before next mole appears
MOLE_SPAWN_DELAY_MAX = 800        # Longest wait. TRY: smaller numbers = chaos!
HIT_FLASH_DURATION_MS = 200       # How long the gold "hit" flash shows

# --- Scoring ---
POINTS_PER_HIT = 10               # Points earned for whacking a mole
POINTS_PER_MISS = -2              # Penalty for clicking empty space (set to 0 to disable)

# --- Fonts ---
# pygame uses font sizes in points. Bigger number = bigger text.
FONT_SIZE_LARGE = 64      # For the "GAME OVER" message
FONT_SIZE_MEDIUM = 36     # For the score and timer
FONT_SIZE_SMALL = 24      # For instructions


# =============================================================================
# THE MOLE CLASS
# =============================================================================
# A "class" is a blueprint for creating objects. Think of it like a cookie
# cutter: the class is the cutter, and each mole we create is a cookie.
# Each mole has its own state (is it visible? when did it appear?) but they
# all share the same behavior (how to draw, how to detect a click).
# -----------------------------------------------------------------------------

class Mole:
    """Represents one mole hole and the mole that pops out of it."""

    def __init__(self, x, y):
        """
        The __init__ method runs automatically when we create a new Mole.
        'self' refers to this specific mole (vs. some other mole).
        x, y are the pixel coordinates where this mole's hole sits.
        """
        self.x = x                    # Horizontal position of the hole
        self.y = y                    # Vertical position of the hole
        self.is_up = False            # True when the mole is popped up
        self.appear_time = 0          # When the mole appeared (for timing)
        self.visible_duration = 0     # How long this mole will stay visible
        self.hit_flash_time = 0       # When this mole was last hit (for flash effect)

    def show(self, current_time):
        """Make this mole pop up out of its hole."""
        self.is_up = True
        self.appear_time = current_time
        # Each appearance has a random duration, so the player can't predict it.
        # random.randint(a, b) gives a random whole number between a and b.
        self.visible_duration = random.randint(
            MOLE_VISIBLE_TIME_MIN, MOLE_VISIBLE_TIME_MAX
        )

    def hide(self):
        """Send the mole back into its hole."""
        self.is_up = False

    def update(self, current_time):
        """
        Called every frame. Checks if the mole has been visible long enough
        and should hide automatically (the player missed it!).
        """
        if self.is_up:
            elapsed = current_time - self.appear_time
            if elapsed >= self.visible_duration:
                self.hide()

    def is_clicked(self, mouse_x, mouse_y):
        """
        Returns True if the given mouse position is inside this mole.
        We use the distance formula: if the click is closer to the mole's
        center than the mole's radius, it's a hit!
        """
        if not self.is_up:
            return False  # Can't whack a mole that isn't there

        # Calculate distance from click to mole's center.
        # The mole appears ABOVE its hole when raised, so we adjust the y.
        mole_center_y = self.y - MOLE_RISE_HEIGHT
        dx = mouse_x - self.x         # Horizontal distance
        dy = mouse_y - mole_center_y  # Vertical distance
        # Pythagoras' theorem: distance² = dx² + dy²
        # We compare squared values to avoid a slow square-root calculation.
        distance_squared = dx * dx + dy * dy
        return distance_squared <= MOLE_RADIUS * MOLE_RADIUS

    def register_hit(self, current_time):
        """Called when the player successfully whacks this mole."""
        self.hide()
        self.hit_flash_time = current_time

    def draw(self, surface, current_time):
        """
        Draw this mole and its hole onto the given surface (the screen).
        The order matters! We draw back-to-front: hole first, then mole on top.
        """
        # Draw the hole (a dark ellipse for depth, then the rim)
        # An ellipse is a squashed circle - perfect for a hole seen from above.
        hole_rect = pygame.Rect(
            self.x - HOLE_RADIUS,           # Left edge
            self.y - HOLE_RADIUS // 3,      # Top edge (hole is short/squashed)
            HOLE_RADIUS * 2,                # Width
            HOLE_RADIUS * 2 // 3            # Height (1/3 as tall as wide)
        )
        pygame.draw.ellipse(surface, COLOR_HOLE_RIM, hole_rect)
        # Draw a slightly smaller dark ellipse inside for the hole's depth
        inner_rect = hole_rect.inflate(-10, -6)  # Shrink by 10px wide, 6px tall
        pygame.draw.ellipse(surface, COLOR_HOLE_DARK, inner_rect)

        # If the mole is up, draw it!
        if self.is_up:
            mole_y = self.y - MOLE_RISE_HEIGHT  # Mole sits above the hole

            # Body (a circle)
            pygame.draw.circle(
                surface, COLOR_MOLE_BODY, (self.x, mole_y), MOLE_RADIUS
            )
            # Belly (a smaller, lighter circle on the lower half)
            pygame.draw.circle(
                surface, COLOR_MOLE_BELLY,
                (self.x, mole_y + MOLE_RADIUS // 3),
                MOLE_RADIUS // 2
            )
            # Eyes (two small black circles)
            eye_offset_x = MOLE_RADIUS // 3
            eye_offset_y = MOLE_RADIUS // 4
            eye_radius = MOLE_RADIUS // 8
            pygame.draw.circle(
                surface, COLOR_MOLE_NOSE,
                (self.x - eye_offset_x, mole_y - eye_offset_y), eye_radius
            )
            pygame.draw.circle(
                surface, COLOR_MOLE_NOSE,
                (self.x + eye_offset_x, mole_y - eye_offset_y), eye_radius
            )
            # Nose (a small dark circle in the middle)
            pygame.draw.circle(
                surface, COLOR_MOLE_NOSE,
                (self.x, mole_y + MOLE_RADIUS // 8),
                MOLE_RADIUS // 6
            )

        # If we recently hit this mole, draw a flash effect.
        # This gives the player satisfying visual feedback!
        flash_elapsed = current_time - self.hit_flash_time
        if flash_elapsed < HIT_FLASH_DURATION_MS:
            # The flash gets bigger and fades over time
            flash_radius = HOLE_RADIUS + (flash_elapsed // 10)
            pygame.draw.circle(
                surface, COLOR_HIT_FLASH,
                (self.x, self.y - MOLE_RISE_HEIGHT // 2),
                flash_radius, 4  # The 4 is the line thickness (0 = filled)
            )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
# Functions are reusable bits of code. Breaking the program into functions
# makes it easier to read and test.
# -----------------------------------------------------------------------------

def create_moles():
    """
    Create all the mole objects in a grid layout.
    Returns a list of Mole objects ready to be used in the game.
    """
    moles = []  # An empty list - we'll add moles to it one by one

    # Calculate spacing so the grid is centered on screen
    # We leave some margin at the top for the score display.
    grid_top_margin = 120
    grid_bottom_margin = 80
    available_height = WINDOW_HEIGHT - grid_top_margin - grid_bottom_margin
    available_width = WINDOW_WIDTH

    # Distance between hole centers
    col_spacing = available_width // (GRID_COLS + 1)
    row_spacing = available_height // (GRID_ROWS + 1)

    # Two nested loops: one for rows, one for columns within each row.
    # range(GRID_ROWS) gives us 0, 1, 2, ..., up to GRID_ROWS-1.
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col_spacing * (col + 1)
            y = grid_top_margin + row_spacing * (row + 1)
            moles.append(Mole(x, y))  # Create a new Mole and add to our list

    return moles


def draw_text_with_shadow(surface, text, font, x, y, color=COLOR_TEXT,
                          shadow_color=COLOR_TEXT_SHADOW, center=False):
    """
    Draw text with a subtle shadow behind it for readability.
    This is a great example of a small reusable function.
    """
    # Render the text twice: once for the shadow, once for the main text
    shadow_surface = font.render(text, True, shadow_color)
    text_surface = font.render(text, True, color)

    if center:
        # If centering, x and y describe the CENTER of the text, not the corner
        text_rect = text_surface.get_rect(center=(x, y))
        shadow_rect = shadow_surface.get_rect(center=(x + 2, y + 2))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
        shadow_rect = shadow_surface.get_rect(topleft=(x + 2, y + 2))

    surface.blit(shadow_surface, shadow_rect)  # blit = "block transfer" = draw
    surface.blit(text_surface, text_rect)


def draw_background(surface):
    """Draw the sky and grass that form the game's backdrop."""
    # Fill the whole screen with sky blue
    surface.fill(COLOR_BACKGROUND)
    # Draw a green rectangle at the bottom for grass
    grass_rect = pygame.Rect(
        0,                              # Left edge
        WINDOW_HEIGHT * 2 // 3,         # Top of grass starts 2/3 down the screen
        WINDOW_WIDTH,                   # Full width
        WINDOW_HEIGHT // 3 + 1          # Reaches the bottom
    )
    pygame.draw.rect(surface, COLOR_GRASS, grass_rect)


# =============================================================================
# THE MAIN GAME FUNCTION
# =============================================================================
# This is where everything comes together. Most games follow this pattern:
#   1. Set up (initialize pygame, create window, load assets)
#   2. Loop forever:
#        a. Handle input (keyboard, mouse, quit events)
#        b. Update game state (move things, check timers)
#        c. Draw everything to the screen
#        d. Wait briefly so we don't run too fast
# -----------------------------------------------------------------------------

def main():
    """The main entry point of our game."""

    # --- SETUP ---
    pygame.init()  # Start up Pygame's internal systems
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # The Clock helps us control how fast the game runs (FPS)
    clock = pygame.time.Clock()

    # Load fonts. None means "use the default system font."
    # TRY: replace None with a font name like "arial" if you have it.
    font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)
    font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
    font_small = pygame.font.SysFont(None, FONT_SIZE_SMALL)

    # --- INITIALIZE GAME STATE ---
    # These variables change as the game progresses.
    # We bundle them into a function so we can reset easily on restart.
    def reset_game():
        return {
            "moles": create_moles(),
            "score": 0,
            "start_time": pygame.time.get_ticks(),  # Time game started (ms)
            "next_spawn_time": pygame.time.get_ticks() + 500,  # When next mole appears
            "game_over": False,
        }

    state = reset_game()

    # --- THE GAME LOOP ---
    # 'while True' loops forever - until we explicitly break out of it.
    running = True
    while running:
        # Get current time in milliseconds since pygame started.
        # We use this for all our timing calculations.
        current_time = pygame.time.get_ticks()

        # ---- 1. HANDLE EVENTS (input from the player) ----
        # pygame stores up "events" that have happened since the last frame.
        # We loop through them and react to each one.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the window's close button
                running = False

            elif event.type == pygame.KEYDOWN:
                # User pressed a key
                if event.key == pygame.K_ESCAPE:
                    running = False  # ESC quits the game
                elif event.key == pygame.K_r and state["game_over"]:
                    # R restarts the game when it's over
                    state = reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN and not state["game_over"]:
                # User clicked the mouse - check if they hit a mole!
                mouse_x, mouse_y = event.pos  # event.pos is a (x, y) tuple
                hit_something = False
                for mole in state["moles"]:
                    if mole.is_clicked(mouse_x, mouse_y):
                        mole.register_hit(current_time)
                        state["score"] += POINTS_PER_HIT
                        hit_something = True
                        break  # Only count one hit per click

                # Penalize misses (clicking empty space)
                if not hit_something:
                    state["score"] += POINTS_PER_MISS

        # ---- 2. UPDATE GAME STATE ----
        # Calculate how much time is left in the round
        elapsed_ms = current_time - state["start_time"]
        time_left_ms = max(0, GAME_DURATION_MS - elapsed_ms)

        if time_left_ms <= 0:
            state["game_over"] = True

        if not state["game_over"]:
            # Update each mole (so they hide themselves after their time is up)
            for mole in state["moles"]:
                mole.update(current_time)

            # Spawn new moles on a random schedule
            if current_time >= state["next_spawn_time"]:
                # Find moles that are currently NOT up (hidden)
                # A "list comprehension" is a compact way to filter a list.
                hidden_moles = [m for m in state["moles"] if not m.is_up]
                if hidden_moles:
                    # Pick a random hidden mole and pop it up
                    chosen = random.choice(hidden_moles)
                    chosen.show(current_time)

                # Schedule the next spawn
                state["next_spawn_time"] = current_time + random.randint(
                    MOLE_SPAWN_DELAY_MIN, MOLE_SPAWN_DELAY_MAX
                )

        # ---- 3. DRAW EVERYTHING ----
        # We draw in layers from back to front.
        draw_background(screen)

        # Draw each mole (they handle drawing their own hole + body)
        for mole in state["moles"]:
            mole.draw(screen, current_time)

        # Draw the score in the top-left
        draw_text_with_shadow(
            screen, f"Score: {state['score']}", font_medium, 20, 20
        )

        # Draw the timer in the top-right
        # Convert milliseconds to seconds for a nicer display
        seconds_left = time_left_ms // 1000
        timer_text = f"Time: {seconds_left}s"
        # We need to know the text width to right-align it
        timer_surface = font_medium.render(timer_text, True, COLOR_TEXT)
        timer_x = WINDOW_WIDTH - timer_surface.get_width() - 20
        draw_text_with_shadow(screen, timer_text, font_medium, timer_x, 20)

        # If the game is over, show the game over screen on top of everything
        if state["game_over"]:
            # Draw a semi-transparent dark overlay so text stands out.
            # We need a separate surface to handle transparency.
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(150)  # 0 = invisible, 255 = fully opaque
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # Show "GAME OVER" centered on screen
            draw_text_with_shadow(
                screen, "GAME OVER", font_large,
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, center=True
            )
            draw_text_with_shadow(
                screen, f"Final Score: {state['score']}", font_medium,
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10, center=True
            )
            draw_text_with_shadow(
                screen, "Press R to play again or ESC to quit", font_small,
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60, center=True
            )

        # pygame uses "double buffering": we draw to a hidden buffer, then
        # flip it to the screen all at once. This prevents flickering.
        pygame.display.flip()

        # ---- 4. CONTROL FRAME RATE ----
        # Tells pygame to wait just long enough that we run at FPS frames/second.
        clock.tick(FPS)

    # --- CLEANUP ---
    # When we exit the loop, shut down pygame cleanly and exit Python.
    pygame.quit()
    sys.exit()


# =============================================================================
# PROGRAM ENTRY POINT
# =============================================================================
# This standard Python idiom means "only run main() if this file is executed
# directly, not if it's imported as a module by another file."
# It's good practice for any Python program.
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()


# =============================================================================
# IDEAS FOR EXPANDING THIS GAME (great practice projects!)
# =============================================================================
# 1. Add sound effects - try pygame.mixer.Sound() for "whack" noises
# 2. Add multiple mole types (a fast golden mole worth more points?)
# 3. Add a "bomb" that pops up sometimes - clicking it ends the game!
# 4. Add increasing difficulty - moles get faster as time runs out
# 5. Save a high score to a text file using Python's open() function
# 6. Replace the drawn moles with image files (pygame.image.load)
# 7. Add a starting menu with a "Play" button
# 8. Track stats: total clicks, accuracy percentage, best streak
# 9. Add a combo system - hits in quick succession score bonus points
# 10. Make the mole "duck" with an animation instead of disappearing instantly
# =============================================================================
