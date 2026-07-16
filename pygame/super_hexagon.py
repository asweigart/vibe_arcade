"""
=============================================================================
SUPER HEXAGON - A Teaching Example
=============================================================================

A simplified version of the game "Super Hexagon" by Terry Cavanagh, written
to teach beginners about game programming concepts.

WHAT YOU'LL LEARN:
  - The "game loop" pattern (input -> update -> draw, repeated forever)
  - Working with angles, rotation, and trigonometry (sine and cosine)
  - Collision detection
  - Procedural generation (creating obstacle patterns by code, not hand)
  - Frame-rate independent movement using "delta time"

HOW TO PLAY:
  - LEFT and RIGHT arrow keys (or A and D) rotate your little triangle
  - Survive as long as you can by dodging the incoming walls
  - Press R to restart after dying, ESC to quit

HOW TO RUN:
  1. Install pygame:    pip install pygame
  2. Run the file:      python super_hexagon.py

EXPERIMENT IDEAS:
  Throughout this file you'll find lots of CONSTANTS at the top of each
  section. These are values you can change to alter how the game feels.
  Try tweaking them and see what happens! Suggestions are in the comments.
=============================================================================
"""

import math      # for sin, cos, pi -- needed to draw rotating shapes
import random    # for picking which walls to spawn
import sys       # for cleanly exiting the program
import pygame    # the game library that handles graphics, input, and timing


# ============================================================================
# DISPLAY CONSTANTS
# ============================================================================
# These control the window itself. Pretty self-explanatory.

WINDOW_WIDTH = 800           # Window width in pixels. Try 1024 for a bigger view.
WINDOW_HEIGHT = 600          # Window height in pixels.
TARGET_FPS = 60              # Frames per second we aim for. 60 is standard.
                             # Try 30 for a "choppier" old-school feel.

WINDOW_TITLE = "Super Hexagon - Teaching Example"


# ============================================================================
# COLOR CONSTANTS
# ============================================================================
# Colors in pygame are (Red, Green, Blue) tuples, each from 0 to 255.
# Try swapping these out for your own color scheme!

# Two alternating background colors for the hexagonal "pie slices"
BG_COLOR_A = (20, 20, 40)        # Dark blue-ish
BG_COLOR_B = (35, 35, 60)        # Slightly lighter blue-ish

# The center hexagon and walls share a color
HEX_COLOR = (255, 80, 120)       # Hot pink. Try (80, 255, 200) for cyan/mint.

# The player's triangle
PLAYER_COLOR = (255, 255, 255)   # White

# Text color (for score and game-over message)
TEXT_COLOR = (255, 255, 255)


# ============================================================================
# GEOMETRY CONSTANTS
# ============================================================================
# The world is built from 6 "slices" radiating out from the center, like a pie.
# Walls are arc-shaped pieces that fill some slices and leave others open.

NUM_SIDES = 6                # 6 = hexagon. Try 4 for a square or 8 for an
                             # octagon. The whole game still works!

# The small hexagon in the middle that the player orbits around
CENTER_HEX_RADIUS = 50       # Bigger = more cramped playing field

# How far walls spawn from the center before moving inward
SPAWN_RADIUS = 700           # Should be larger than the screen so walls
                             # appear from off-screen

# The thickness of each wall (in pixels of radial distance)
WALL_THICKNESS = 30          # Thicker walls are easier to see but harder
                             # to dodge through gaps. Try 20 or 50.

# Wall outline thickness for the center hexagon's border
HEX_BORDER_THICKNESS = 4


# ============================================================================
# PLAYER CONSTANTS
# ============================================================================

# How far from the center the player orbits
PLAYER_ORBIT_RADIUS = CENTER_HEX_RADIUS + 15

# Size of the player triangle
PLAYER_SIZE = 10             # Try 15 for a bigger, easier-to-see player

# How fast the player rotates around the center, in degrees per second
PLAYER_ROTATION_SPEED = 280  # Higher = more responsive but harder to control.
                             # Try 200 for slow & steady, 400 for twitchy.


# ============================================================================
# WALL / DIFFICULTY CONSTANTS
# ============================================================================

# How fast walls move toward the center, in pixels per second.
# This is the main "difficulty" knob -- crank it up for a hardcore mode!
WALL_SPEED = 180             # Try 120 for easy, 250 for "hexagonest" mode

# Time between spawning new groups of walls (in seconds)
WALL_SPAWN_INTERVAL = 1.2    # Lower = more frequent waves = harder.
                             # Try 0.8 for chaos or 2.0 for relaxed.

# How many of the 6 slices each wave fills (the rest are gaps to dodge through).
# Must be less than NUM_SIDES, otherwise there's no gap to escape through!
MIN_WALLS_PER_WAVE = 3       # Easier waves
MAX_WALLS_PER_WAVE = 5       # Hardest waves -- only 1 gap!

# Speed at which the entire world rotates, in degrees per second.
# This makes things much harder because "left" and "right" keep shifting.
WORLD_ROTATION_SPEED = 25    # Try 0 for no rotation (much easier),
                             # or 60 for a dizzying spin.

# Whether the world occasionally reverses rotation direction
WORLD_REVERSES = True        # Set to False to keep rotation steady
WORLD_REVERSE_INTERVAL = 6.0 # Seconds between possible direction flips


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
# Small utilities used throughout the game. Keeping them at the top makes
# the main game logic below easier to read.

def polar_to_cartesian(center_x, center_y, radius, angle_degrees):
    """
    Converts a "polar" coordinate (distance + angle) into a regular (x, y)
    screen coordinate. This is the heart of any game with rotation.

    Imagine standing at (center_x, center_y) and walking `radius` pixels
    in the direction of `angle_degrees`. This function tells you where
    you'd end up.

    Math note: pygame's y-axis points DOWN (not up like in math class),
    which is why some games look "flipped" without thinking about it.
    For our purposes here it doesn't matter -- the game is symmetric.
    """
    angle_radians = math.radians(angle_degrees)  # trig functions need radians
    x = center_x + radius * math.cos(angle_radians)
    y = center_y + radius * math.sin(angle_radians)
    return (x, y)


def get_slice_polygon(center_x, center_y, slice_index, inner_radius, outer_radius, world_rotation):
    """
    Returns the 4 corner points of one "arc segment" -- a piece of the
    pie that goes from inner_radius to outer_radius and spans one slice.

    We use this both for drawing the colored background slices AND
    for drawing walls. A wall is just a slice with a small radial range.
    """
    # The angle each slice covers. With 6 slices, that's 60 degrees each.
    slice_angle = 360 / NUM_SIDES

    # The starting and ending angles for this particular slice.
    # Adding world_rotation makes the whole pattern spin.
    start_angle = slice_index * slice_angle + world_rotation
    end_angle = start_angle + slice_angle

    # Build the 4 corners going around the segment:
    #   inner-start -> outer-start -> outer-end -> inner-end
    # That order matters! Pygame draws polygons by connecting points in
    # the order you give them, so jumbling the order gives a bow-tie shape.
    return [
        polar_to_cartesian(center_x, center_y, inner_radius, start_angle),
        polar_to_cartesian(center_x, center_y, outer_radius, start_angle),
        polar_to_cartesian(center_x, center_y, outer_radius, end_angle),
        polar_to_cartesian(center_x, center_y, inner_radius, end_angle),
    ]


def angle_in_slice(angle_degrees, slice_index, world_rotation):
    """
    Returns True if the given angle falls inside the given slice.
    Used for collision detection: we check which slice the player is in,
    then see if any wall is currently occupying that slice at the player's
    distance from center.
    """
    slice_angle = 360 / NUM_SIDES
    slice_start = (slice_index * slice_angle + world_rotation) % 360
    slice_end = (slice_start + slice_angle) % 360

    # Normalize the test angle to [0, 360)
    a = angle_degrees % 360

    # Handle the case where the slice wraps past 360 (e.g. starts at 350,
    # ends at 50). Without this special case, we'd get the wrong answer.
    if slice_start < slice_end:
        return slice_start <= a < slice_end
    else:
        return a >= slice_start or a < slice_end


# ============================================================================
# THE WALL CLASS
# ============================================================================
# A "Wall" is one obstacle: a single arc-segment in one slice that moves
# toward the center over time. A "wave" is several walls spawned together.

class Wall:
    """One arc-shaped obstacle that closes in on the player."""

    def __init__(self, slice_index, spawn_radius):
        # Which of the 6 slices this wall lives in
        self.slice_index = slice_index

        # The wall's *outer* edge starts at spawn_radius and shrinks over time.
        # The inner edge is always WALL_THICKNESS less than the outer edge.
        self.outer_radius = spawn_radius

    def update(self, delta_time):
        """
        Move the wall closer to the center.

        delta_time is the number of seconds since the last frame. We multiply
        by it so movement happens at the same real-world speed regardless of
        how fast the computer is running. This is a critical concept in games.
        """
        self.outer_radius -= WALL_SPEED * delta_time

    @property
    def inner_radius(self):
        """The inner edge of the wall, which is what the player collides with."""
        return self.outer_radius - WALL_THICKNESS

    def is_off_screen(self):
        """Returns True if this wall has shrunk past the center hexagon
        and is no longer relevant. We can delete it to free up memory."""
        return self.outer_radius < CENTER_HEX_RADIUS


# ============================================================================
# THE GAME CLASS
# ============================================================================
# Wrapping everything in a class keeps the code organized and makes it easy
# to "reset" by just creating a fresh Game object.

class Game:

    def __init__(self, screen):
        self.screen = screen
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2

        # Fonts for drawing the score and game-over message
        self.font_small = pygame.font.SysFont(None, 32)
        self.font_large = pygame.font.SysFont(None, 72)

        # Game state -- reset() initializes all the per-game variables
        self.reset()

    def reset(self):
        """Start a new game. Called at the start and whenever the player dies."""

        # The player's angle around the center, in degrees.
        # 270 degrees = "top" of the screen (because pygame's y-axis is flipped).
        self.player_angle = 270.0

        # All currently-active walls
        self.walls = []

        # Time tracking
        self.time_since_spawn = 0.0    # for deciding when to spawn next wave
        self.time_since_reverse = 0.0  # for deciding when world might flip
        self.elapsed = 0.0             # total survival time, used as score

        # World rotation
        self.world_rotation = 0.0
        self.world_rotation_direction = 1  # 1 or -1

        # Are we alive? When False, we show the game-over screen.
        self.alive = True

    # ------------------------------------------------------------------
    # Wall spawning
    # ------------------------------------------------------------------

    def spawn_wave(self):
        """
        Create a new wave of walls. We pick a random number of slices to fill
        (leaving the rest as gaps), then create a wall in each chosen slice.
        """
        num_walls = random.randint(MIN_WALLS_PER_WAVE, MAX_WALLS_PER_WAVE)

        # Pick `num_walls` distinct slices out of the available ones.
        # random.sample guarantees no duplicates, so we don't double up walls.
        chosen_slices = random.sample(range(NUM_SIDES), num_walls)

        for slice_index in chosen_slices:
            self.walls.append(Wall(slice_index, SPAWN_RADIUS))

    # ------------------------------------------------------------------
    # Update (game logic per frame)
    # ------------------------------------------------------------------

    def update(self, delta_time, keys):
        """
        Run one tick of game logic. Called once per frame.

        delta_time: seconds since last frame (small number like 0.0167 at 60fps)
        keys: pygame's key-state dictionary
        """
        if not self.alive:
            return  # Don't update anything while dead -- frozen game-over screen

        self.elapsed += delta_time

        # --- Player rotation ---
        # Subtract from angle to go counterclockwise (matches arrow direction
        # visually). The "or" lets either arrow keys or WASD work.
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_angle -= PLAYER_ROTATION_SPEED * delta_time
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_angle += PLAYER_ROTATION_SPEED * delta_time

        # Keep the angle in [0, 360) so collision math is simpler
        self.player_angle %= 360

        # --- World rotation ---
        self.world_rotation += WORLD_ROTATION_SPEED * self.world_rotation_direction * delta_time
        self.world_rotation %= 360

        # Periodically maybe reverse the world's spin direction
        if WORLD_REVERSES:
            self.time_since_reverse += delta_time
            if self.time_since_reverse >= WORLD_REVERSE_INTERVAL:
                self.time_since_reverse = 0.0
                # 50% chance to flip; otherwise continue current direction
                if random.random() < 0.5:
                    self.world_rotation_direction *= -1

        # --- Wall spawning ---
        self.time_since_spawn += delta_time
        if self.time_since_spawn >= WALL_SPAWN_INTERVAL:
            self.time_since_spawn = 0.0
            self.spawn_wave()

        # --- Update walls ---
        for wall in self.walls:
            wall.update(delta_time)

        # Remove walls that have passed through the center.
        # This list comprehension keeps only walls that are still on-screen.
        self.walls = [w for w in self.walls if not w.is_off_screen()]

        # --- Collision detection ---
        self.check_collision()

    def check_collision(self):
        """
        Determine whether the player is currently overlapping any wall.

        Approach: the player sits at distance PLAYER_ORBIT_RADIUS from the
        center, at angle self.player_angle. A wall hits the player if:
          1) The player's angle falls inside the wall's slice, AND
          2) PLAYER_ORBIT_RADIUS is between the wall's inner & outer radius.
        """
        for wall in self.walls:
            # Quick radial check first -- usually rules out most walls fast.
            if wall.inner_radius <= PLAYER_ORBIT_RADIUS <= wall.outer_radius:
                # The wall is at the player's distance. Check the angle.
                if angle_in_slice(self.player_angle, wall.slice_index, self.world_rotation):
                    self.alive = False
                    return  # No need to check further; we're already dead

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self):
        """Render everything to the screen. Called once per frame."""
        # Order matters: things drawn later appear on top of things drawn earlier.
        self.draw_background_slices()
        self.draw_walls()
        self.draw_center_hexagon()
        self.draw_player()
        self.draw_hud()

        if not self.alive:
            self.draw_game_over()

    def draw_background_slices(self):
        """Draw the alternating-color pie slices that make up the background."""
        for i in range(NUM_SIDES):
            # Alternate colors for visual interest
            color = BG_COLOR_A if i % 2 == 0 else BG_COLOR_B

            # Each background slice goes from the center hexagon's edge
            # all the way out to a huge radius (so it covers the screen).
            points = get_slice_polygon(
                self.center_x, self.center_y,
                slice_index=i,
                inner_radius=0,
                outer_radius=SPAWN_RADIUS * 1.5,  # over-sized to cover corners
                world_rotation=self.world_rotation,
            )
            pygame.draw.polygon(self.screen, color, points)

    def draw_walls(self):
        """Draw each wall as a colored arc-segment polygon."""
        for wall in self.walls:
            # Don't try to draw walls that have shrunk to nothing yet
            if wall.inner_radius <= 0:
                continue

            points = get_slice_polygon(
                self.center_x, self.center_y,
                slice_index=wall.slice_index,
                inner_radius=wall.inner_radius,
                outer_radius=wall.outer_radius,
                world_rotation=self.world_rotation,
            )
            pygame.draw.polygon(self.screen, HEX_COLOR, points)

    def draw_center_hexagon(self):
        """Draw the small hexagon at the center of the play field."""
        # Build the 6 corners of the central hexagon
        corners = []
        for i in range(NUM_SIDES):
            angle = i * (360 / NUM_SIDES) + self.world_rotation
            corners.append(polar_to_cartesian(
                self.center_x, self.center_y, CENTER_HEX_RADIUS, angle
            ))

        # Filled background-colored hexagon
        pygame.draw.polygon(self.screen, BG_COLOR_A, corners)
        # Pink outline (drawing the polygon with a "width" gives an outline)
        pygame.draw.polygon(self.screen, HEX_COLOR, corners, HEX_BORDER_THICKNESS)

    def draw_player(self):
        """Draw the player as a small triangle pointing outward from center."""
        # The triangle has 3 corners: a "tip" pointing away from the center,
        # and two "base" corners spread to the sides at the orbit radius.
        tip = polar_to_cartesian(
            self.center_x, self.center_y,
            PLAYER_ORBIT_RADIUS + PLAYER_SIZE,
            self.player_angle,
        )
        # Spread the base corners 8 degrees to either side -- this is a
        # purely visual choice. Tweak for a fatter or skinnier triangle.
        left_base = polar_to_cartesian(
            self.center_x, self.center_y,
            PLAYER_ORBIT_RADIUS,
            self.player_angle - 8,
        )
        right_base = polar_to_cartesian(
            self.center_x, self.center_y,
            PLAYER_ORBIT_RADIUS,
            self.player_angle + 8,
        )
        pygame.draw.polygon(self.screen, PLAYER_COLOR, [tip, left_base, right_base])

    def draw_hud(self):
        """Draw the score (your survival time)."""
        score_text = f"Time: {self.elapsed:.1f}s"
        surface = self.font_small.render(score_text, True, TEXT_COLOR)
        # Position in top-left with a small margin
        self.screen.blit(surface, (15, 10))

    def draw_game_over(self):
        """Show the game-over message overlay."""
        # Big "GAME OVER" text, centered
        big = self.font_large.render("GAME OVER", True, TEXT_COLOR)
        big_rect = big.get_rect(center=(self.center_x, self.center_y - 40))
        self.screen.blit(big, big_rect)

        # Smaller restart instruction below
        small_text = f"Survived {self.elapsed:.1f}s   -   Press R to restart, ESC to quit"
        small = self.font_small.render(small_text, True, TEXT_COLOR)
        small_rect = small.get_rect(center=(self.center_x, self.center_y + 30))
        self.screen.blit(small, small_rect)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
# This is what runs when you do `python super_hexagon.py`. It sets up pygame,
# creates the Game, and runs the main loop.

def main():
    # Initialize pygame -- this gets the graphics, sound, and input ready.
    pygame.init()

    # Create the window we'll draw into
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # The Clock helps us measure frame time and limit our FPS
    clock = pygame.time.Clock()

    game = Game(screen)

    # ---- The Game Loop ----
    # This is the heart of every real-time game. Every iteration of this
    # loop is ONE FRAME. We do four things per frame:
    #   1. Measure how much time passed since last frame (delta_time)
    #   2. Process input events (keypresses, window close button, etc.)
    #   3. Update game state
    #   4. Draw the new frame
    # Then we repeat until the player quits.

    running = True
    while running:
        # 1. Frame timing.
        # clock.tick(TARGET_FPS) sleeps just long enough to hit the target FPS,
        # and returns how many milliseconds passed since the last call.
        # We divide by 1000 to convert ms to seconds for delta_time.
        delta_time = clock.tick(TARGET_FPS) / 1000.0

        # 2. Process events.
        # pygame.event.get() returns everything that happened since last frame:
        # key presses, mouse clicks, window close, etc.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the window's close button
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and not game.alive:
                    # Restart only works while on the game-over screen
                    game.reset()

        # The "key state" tells us which keys are currently held down.
        # This is different from KEYDOWN events: KEYDOWN fires once when the
        # key is first pressed, but get_pressed() tells us "right now, is it
        # being held?" That's what we want for smooth player rotation.
        keys = pygame.key.get_pressed()

        # 3. Update game logic
        game.update(delta_time, keys)

        # 4. Draw the new frame
        game.draw()

        # Send the freshly drawn frame to the actual screen.
        # (We've been drawing to an off-screen buffer; this swaps it in.)
        pygame.display.flip()

    # Clean shutdown
    pygame.quit()
    sys.exit()


# This idiom means "only run main() if this file is being run directly,
# not if it's being imported by another file as a library."
if __name__ == "__main__":
    main()
