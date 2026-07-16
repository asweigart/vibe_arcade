"""
================================================================================
 ENDLESS RUNNER - A Beginner-Friendly Pygame Teaching Example
================================================================================

WHAT IS THIS?
    A simple "endless runner" game (think Chrome Dinosaur, Subway Surfers, etc.)
    where a player character runs forward forever, jumping over obstacles that
    come at them. The longer you survive, the higher your score.

WHAT YOU'LL LEARN BY READING / TWEAKING THIS FILE:
    * The "game loop" pattern (events -> update -> draw -> repeat)
    * How to use classes to organize game objects
    * Basic 2D physics (gravity, jumping, velocity)
    * Collision detection using rectangles
    * How constants make games easy to tune and balance
    * How difficulty scaling keeps a game interesting

HOW TO RUN IT:
    1. Install Python 3.8 or newer.
    2. Install pygame:    pip install pygame
    3. Run this file:     python endless_runner.py

HOW TO PLAY:
    SPACE or UP ARROW  -> Jump (you can double-jump!)
    DOWN ARROW         -> Duck (slide under flying obstacles)
    R                  -> Restart after game over
    ESC                -> Quit

EXPERIMENT!
    Almost every number in this file is a CONSTANT defined near the top, with a
    comment suggesting things to try. Change them, run the game, see what
    happens. That's the fastest way to build intuition for game design.
================================================================================
"""

# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
# `pygame` is the library that handles drawing, sound, and input for us.
# `random` lets us make decisions that aren't predictable (like which obstacle
# to spawn next). `sys` is used for cleanly exiting the program.
import pygame
import random
import sys


# ==============================================================================
# CONSTANTS - Tweak these to change how the game looks and feels!
# ==============================================================================
# A "constant" is a value we set once and don't change while the game is
# running. Putting them all at the top makes them easy to find and adjust.
# Tradition is to write constant names in ALL_CAPS.

# ------- Window / Display -----------------------------------------------------
WINDOW_WIDTH = 900          # Width of the game window in pixels.
                            # TRY: 600 (smaller) or 1280 (widescreen).
WINDOW_HEIGHT = 400         # Height of the game window in pixels.
                            # TRY: 300 (more cramped) or 600 (more vertical space).
WINDOW_TITLE = "Endless Runner"  # The text shown in the window's title bar.
TARGET_FPS = 60             # Frames per second. 60 is smooth for most games.
                            # TRY: 30 (choppier, more retro) or 120 (very smooth).

# ------- Colors (Red, Green, Blue) values from 0 to 255 -----------------------
# Each color is a tuple of three numbers. Think "how much red, green, blue."
# (0,0,0) is pure black, (255,255,255) is pure white. Mix to taste.
COLOR_SKY = (135, 206, 235)        # Pleasant daytime sky blue. TRY (10,10,40) for night!
COLOR_GROUND = (160, 110, 60)      # Earthy brown for the ground.
COLOR_GROUND_LINE = (80, 50, 20)   # Darker line where ground meets sky.
COLOR_PLAYER = (50, 50, 80)        # Dark blue-gray for the player.
COLOR_PLAYER_EYE = (255, 255, 255) # White eye on the player.
COLOR_OBSTACLE_GROUND = (60, 130, 60)  # Green cactus-like ground obstacle.
COLOR_OBSTACLE_AIR = (180, 60, 60)     # Red flying obstacle.
COLOR_CLOUD = (255, 255, 255)      # White clouds.
COLOR_TEXT = (30, 30, 30)          # Dark text for HUD.
COLOR_TEXT_BIG = (200, 30, 30)     # Red for the GAME OVER message.

# ------- Ground / World layout ------------------------------------------------
GROUND_HEIGHT = 60          # How tall the ground strip at the bottom is.
                            # TRY: 30 (slim) or 120 (more dirt visible).

# ------- Player properties ----------------------------------------------------
PLAYER_X = 100              # Player's horizontal position. They never move
                            # left/right; the WORLD scrolls past them instead.
                            # TRY: 200 to give yourself more reaction time.
PLAYER_WIDTH = 40           # Player width in pixels.
PLAYER_HEIGHT = 60          # Player height when standing.
PLAYER_DUCK_HEIGHT = 30     # Player height when ducking (shorter = harder to hit).

PLAYER_GRAVITY = 0.9        # How strongly gravity pulls the player down each frame.
                            # TRY: 0.4 (floaty moon jump) or 1.5 (heavy, snappy).
PLAYER_JUMP_STRENGTH = -16  # NEGATIVE because in pygame, Y increases DOWNWARD.
                            # So negative velocity = moving UP. A bigger
                            # absolute number = higher jump.
                            # TRY: -10 (tiny hops) or -22 (big floaty leaps).
PLAYER_MAX_JUMPS = 2        # 1 = single jump only. 2 = double jump.
                            # TRY: 3 for a triple jump and very forgiving play.

# ------- Obstacle properties --------------------------------------------------
OBSTACLE_MIN_GAP = 350      # Minimum pixels between obstacles. Smaller = harder.
OBSTACLE_MAX_GAP = 700      # Maximum pixels between obstacles.
                            # TRY making MIN and MAX equal for predictable rhythm.

# Ground obstacles (jump OVER these)
GROUND_OBSTACLE_MIN_WIDTH = 20
GROUND_OBSTACLE_MAX_WIDTH = 45
GROUND_OBSTACLE_MIN_HEIGHT = 30
GROUND_OBSTACLE_MAX_HEIGHT = 70   # Taller ones are harder to clear.

# Air obstacles (duck UNDER these)
AIR_OBSTACLE_WIDTH = 50
AIR_OBSTACLE_HEIGHT = 25
AIR_OBSTACLE_FLOAT_HEIGHT = 55    # How high above the ground the air obstacle sits.
                                  # MUST be high enough that ducking lets you
                                  # pass safely, but low enough that it hits a
                                  # standing player.
AIR_OBSTACLE_CHANCE = 0.3   # Probability (0.0 to 1.0) that a new obstacle is
                            # an air obstacle. 0.0 = never any flying ones.
                            # TRY: 0.5 for a real mix, or 0.0 for jump-only.

# ------- Difficulty scaling ---------------------------------------------------
# The world starts slow and speeds up over time, which is what makes endless
# runners feel exciting. These constants control that ramp.
START_SPEED = 6.0           # World scroll speed at the start of a run (pixels/frame).
                            # TRY: 3.0 (very chill start) or 10.0 (instant chaos).
MAX_SPEED = 18.0            # Speed will not increase past this. Without a cap,
                            # the game eventually becomes literally unplayable.
                            # TRY: 12.0 for a more relaxed top end.
SPEED_INCREASE_PER_SECOND = 0.15  # How much speed gains per second of survival.
                                  # TRY: 0.0 to disable scaling entirely.

# ------- Scoring --------------------------------------------------------------
SCORE_PER_SECOND = 10       # Points awarded for each second alive.
                            # TRY: 100 for big satisfying numbers.

# ------- Clouds (decorative background) ---------------------------------------
CLOUD_COUNT = 4             # How many clouds drift across the sky.
CLOUD_SPEED_FACTOR = 0.2    # Clouds move slower than the ground (parallax effect).
                            # 1.0 = same speed, 0.0 = totally still.
                            # TRY: 0.5 to make them more noticeable.


# ==============================================================================
# DERIVED CONSTANTS - Calculated from the values above.
# ==============================================================================
# It would be a pain to manually keep these in sync, so we compute them.
# `GROUND_Y` is the Y coordinate of the top of the ground strip - the line
# things "stand on."
GROUND_Y = WINDOW_HEIGHT - GROUND_HEIGHT


# ==============================================================================
# THE PLAYER CLASS
# ==============================================================================
# A "class" is a blueprint for an object. The Player class describes everything
# our hero can do: jump, duck, fall under gravity, get drawn to the screen.
# Using a class keeps related data (position, velocity) and behavior (jump,
# update) bundled together neatly.
class Player:
    def __init__(self):
        """The __init__ method runs once when we create a new Player.
        It sets up the player's starting state."""
        # Position: (x stays fixed, y will change as we jump and fall)
        self.x = PLAYER_X
        self.y = GROUND_Y - PLAYER_HEIGHT  # Start standing on the ground.

        # Size: changes between standing and ducking.
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT

        # Velocity: how fast we're moving vertically. Positive = down, negative = up.
        self.velocity_y = 0

        # Tracks how many jumps we've used since last touching the ground.
        # Resets to 0 when we land. This is what enables double-jumping.
        self.jumps_used = 0

        # Are we currently holding the duck button?
        self.is_ducking = False

    def jump(self):
        """Make the player jump - but only if we have jumps left in our budget."""
        if self.jumps_used < PLAYER_MAX_JUMPS:
            # Setting velocity to a negative number flings us upward.
            self.velocity_y = PLAYER_JUMP_STRENGTH
            self.jumps_used += 1

    def start_duck(self):
        """Crouch down. Only works while on the ground; ducking mid-air feels weird."""
        # The `_is_on_ground()` helper checks if we're currently touching the ground.
        if self._is_on_ground():
            self.is_ducking = True
            self.height = PLAYER_DUCK_HEIGHT
            # Adjust Y so we're still standing on the ground after shrinking.
            # (Otherwise we'd float a bit because our top-left corner is the
            # anchor point.)
            self.y = GROUND_Y - self.height

    def stop_duck(self):
        """Stand back up to full height."""
        self.is_ducking = False
        self.height = PLAYER_HEIGHT
        # Re-anchor to the ground if we were on it.
        if self._is_on_ground():
            self.y = GROUND_Y - self.height

    def _is_on_ground(self):
        """Returns True if the player's feet are touching the ground.
        The leading underscore is a Python convention meaning 'this is for
        internal use by the class'."""
        return self.y + self.height >= GROUND_Y

    def update(self):
        """Called once per frame. Handles physics: gravity, falling, landing."""
        # Apply gravity by adding to our downward velocity each frame.
        # Over time this makes us fall faster and faster (until we land).
        self.velocity_y += PLAYER_GRAVITY

        # Move by our current velocity.
        self.y += self.velocity_y

        # Did we hit (or pass through) the ground? If so, snap to it.
        if self.y + self.height >= GROUND_Y:
            self.y = GROUND_Y - self.height
            self.velocity_y = 0
            # Refresh our jump budget now that we've landed.
            self.jumps_used = 0

    def get_rect(self):
        """Return a pygame Rect for collision detection.
        A Rect is just a rectangle: (x, y, width, height)."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        """Draw the player onto the given surface (the screen)."""
        # Body: a solid colored rectangle.
        pygame.draw.rect(surface, COLOR_PLAYER, self.get_rect())

        # Eye: a small white square so the player has a sense of "facing right."
        # Position it relative to the body so it moves with the player.
        eye_size = 6
        eye_x = self.x + self.width - eye_size - 6
        eye_y = self.y + 10 if not self.is_ducking else self.y + 6
        pygame.draw.rect(surface, COLOR_PLAYER_EYE,
                         (eye_x, eye_y, eye_size, eye_size))


# ==============================================================================
# THE OBSTACLE CLASS
# ==============================================================================
# Obstacles come in two flavors:
#   - "ground": a tall thing on the ground you must JUMP over.
#   - "air":    a flying thing at head height you must DUCK under.
class Obstacle:
    def __init__(self, x, kind):
        """Create a new obstacle. `kind` is the string "ground" or "air"."""
        self.kind = kind

        if kind == "ground":
            # Pick a random size within our configured range.
            # `random.randint(a, b)` returns a whole number between a and b.
            self.width = random.randint(GROUND_OBSTACLE_MIN_WIDTH,
                                        GROUND_OBSTACLE_MAX_WIDTH)
            self.height = random.randint(GROUND_OBSTACLE_MIN_HEIGHT,
                                         GROUND_OBSTACLE_MAX_HEIGHT)
            # Sit on the ground.
            self.x = x
            self.y = GROUND_Y - self.height
            self.color = COLOR_OBSTACLE_GROUND
        else:  # "air"
            self.width = AIR_OBSTACLE_WIDTH
            self.height = AIR_OBSTACLE_HEIGHT
            self.x = x
            # Float at a fixed height above the ground.
            self.y = GROUND_Y - AIR_OBSTACLE_FLOAT_HEIGHT
            self.color = COLOR_OBSTACLE_AIR

    def update(self, world_speed):
        """Move the obstacle leftward at the current world speed."""
        self.x -= world_speed

    def is_off_screen(self):
        """Has this obstacle scrolled off the left edge? If so, we can delete it."""
        return self.x + self.width < 0

    def get_rect(self):
        """Rectangle for collision detection."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        """Draw the obstacle as a colored rectangle."""
        pygame.draw.rect(surface, self.color, self.get_rect())


# ==============================================================================
# THE CLOUD CLASS
# ==============================================================================
# Clouds are purely decorative - they don't interact with the player at all.
# Their only job is to make the world feel alive. Notice how much simpler this
# class is than Obstacle: no collision, no special types, just drift and draw.
class Cloud:
    def __init__(self, x=None):
        """If no x is given, pick a random one (used at game start)."""
        if x is None:
            self.x = random.randint(0, WINDOW_WIDTH)
        else:
            self.x = x
        # Clouds live in the upper portion of the sky.
        self.y = random.randint(20, WINDOW_HEIGHT // 2 - 40)
        self.width = random.randint(60, 120)
        self.height = random.randint(20, 35)

    def update(self, world_speed):
        """Drift left, but slower than the ground for a parallax effect.
        Parallax = far-away things appear to move slower than near things.
        It's a cheap, classic trick for adding depth to 2D games."""
        self.x -= world_speed * CLOUD_SPEED_FACTOR
        # When a cloud goes off the left edge, wrap it to the right side
        # so the sky is always populated.
        if self.x + self.width < 0:
            self.x = WINDOW_WIDTH + random.randint(0, 200)
            self.y = random.randint(20, WINDOW_HEIGHT // 2 - 40)
            self.width = random.randint(60, 120)
            self.height = random.randint(20, 35)

    def draw(self, surface):
        """Draw a fluffy-looking cloud as a few overlapping ellipses."""
        # An ellipse is just an oval. Drawing 3 overlapping ones makes
        # a passable cloud shape without needing any image files.
        pygame.draw.ellipse(surface, COLOR_CLOUD,
                            (self.x, self.y, self.width, self.height))
        pygame.draw.ellipse(surface, COLOR_CLOUD,
                            (self.x + self.width // 4, self.y - self.height // 3,
                             self.width // 2, self.height))
        pygame.draw.ellipse(surface, COLOR_CLOUD,
                            (self.x + self.width // 2, self.y,
                             self.width // 2, self.height))


# ==============================================================================
# THE GAME CLASS
# ==============================================================================
# The Game class is the conductor of the orchestra. It owns the player,
# the obstacles, the score, and runs the main game loop.
class Game:
    def __init__(self):
        """Set up pygame and create the window."""
        pygame.init()  # Initializes all the pygame modules. Always call this first.

        # Create the window we'll be drawing into.
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)

        # The Clock object lets us cap the frame rate so the game runs at
        # roughly the same speed on every computer.
        self.clock = pygame.time.Clock()

        # Fonts for drawing text. `None` means "use the default system font."
        self.font_small = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 72)

        # Initialize game state by calling reset().
        self.reset()

    def reset(self):
        """Start (or restart) a fresh run. Called at game start and after a
        game over when the player hits R."""
        self.player = Player()
        self.obstacles = []  # An empty list - we'll add obstacles as we go.
        # Pre-populate clouds so the sky isn't empty on frame 1.
        self.clouds = [Cloud() for _ in range(CLOUD_COUNT)]

        self.world_speed = START_SPEED
        self.score = 0.0  # Float, because we add fractional points each frame.
        self.time_alive = 0.0  # Seconds since this run started.
        self.game_over = False

        # Decide where the FIRST obstacle should appear. After that, each new
        # obstacle's position is based on the previous one.
        self.next_obstacle_x = WINDOW_WIDTH + 200

    def spawn_obstacle(self):
        """Add a new obstacle at `self.next_obstacle_x`, then schedule the
        position of the one after it."""
        # Pick ground or air randomly, weighted by AIR_OBSTACLE_CHANCE.
        # `random.random()` returns a float between 0.0 and 1.0.
        if random.random() < AIR_OBSTACLE_CHANCE:
            kind = "air"
        else:
            kind = "ground"

        self.obstacles.append(Obstacle(self.next_obstacle_x, kind))

        # Choose a gap to the next one, then advance the spawn point.
        gap = random.randint(OBSTACLE_MIN_GAP, OBSTACLE_MAX_GAP)
        self.next_obstacle_x += gap

    def handle_events(self):
        """Process all input from the keyboard, mouse, and window controls.
        This is the 'EVENTS' part of the classic events -> update -> draw loop."""
        # `pygame.event.get()` returns a list of everything that happened since
        # last frame: key presses, mouse clicks, the X button being clicked, etc.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the window's close button.
                self.quit()

            elif event.type == pygame.KEYDOWN:
                # A key was just pressed (this fires once per press, not while held).
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_r and self.game_over:
                    # Restart only if we're currently dead.
                    self.reset()
                elif not self.game_over:
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        self.player.jump()
                    elif event.key == pygame.K_DOWN:
                        self.player.start_duck()

            elif event.type == pygame.KEYUP:
                # A key was just released.
                if event.key == pygame.K_DOWN:
                    self.player.stop_duck()

    def update(self, delta_time):
        """Advance the game by `delta_time` seconds.
        `delta_time` is the time since the last frame, used to keep movement
        consistent regardless of frame rate."""
        if self.game_over:
            return  # Frozen on the game over screen until R is pressed.

        # --- Track time and score ---
        self.time_alive += delta_time
        self.score += SCORE_PER_SECOND * delta_time

        # --- Speed up the world over time ---
        # We use min() to clamp the speed at MAX_SPEED.
        self.world_speed = min(
            START_SPEED + SPEED_INCREASE_PER_SECOND * self.time_alive,
            MAX_SPEED
        )

        # --- Update the player and the world ---
        self.player.update()

        for cloud in self.clouds:
            cloud.update(self.world_speed)

        for obstacle in self.obstacles:
            obstacle.update(self.world_speed)

        # Remove obstacles that have scrolled off the left side. We use a
        # "list comprehension" - a compact way to build a new list including
        # only the items we want to keep.
        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]

        # Spawn new obstacles. We use a `while` loop instead of `if` so that on
        # very low frame rates we still keep up. (Usually only spawns once.)
        # We also subtract world_speed from next_obstacle_x to make spawning
        # frame-rate aware - the spawn point "moves" toward the screen.
        self.next_obstacle_x -= self.world_speed
        while self.next_obstacle_x <= WINDOW_WIDTH:
            self.spawn_obstacle()

        # --- Check for collisions ---
        # `colliderect` returns True if two pygame Rects overlap.
        player_rect = self.player.get_rect()
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle.get_rect()):
                self.game_over = True
                break  # No need to check more once we've crashed.

    def draw(self):
        """Render everything to the screen.
        This is the 'DRAW' part of the events -> update -> draw loop."""
        # 1. Sky - fill the entire window with the sky color first.
        #    Whatever we draw next is layered ON TOP of this.
        self.screen.fill(COLOR_SKY)

        # 2. Clouds - drawn before the ground so they appear "behind" it
        #    (though in this game they're high in the sky anyway).
        for cloud in self.clouds:
            cloud.draw(self.screen)

        # 3. Ground - a brown strip at the bottom...
        pygame.draw.rect(self.screen, COLOR_GROUND,
                         (0, GROUND_Y, WINDOW_WIDTH, GROUND_HEIGHT))
        # ...and a darker line at the top of it for definition.
        pygame.draw.line(self.screen, COLOR_GROUND_LINE,
                         (0, GROUND_Y), (WINDOW_WIDTH, GROUND_Y), 2)

        # 4. Obstacles
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        # 5. Player (on top, so they're never hidden behind anything).
        self.player.draw(self.screen)

        # 6. HUD (Heads-Up Display) - score and speed in the top-left.
        score_surface = self.font_small.render(
            f"Score: {int(self.score)}", True, COLOR_TEXT
        )
        speed_surface = self.font_small.render(
            f"Speed: {self.world_speed:.1f}", True, COLOR_TEXT
        )
        self.screen.blit(score_surface, (10, 10))
        self.screen.blit(speed_surface, (10, 36))

        # 7. Game-over overlay
        if self.game_over:
            self._draw_game_over()

        # `pygame.display.flip()` actually puts everything we just drew onto
        # the visible screen. Until you call this, the user sees nothing new.
        pygame.display.flip()

    def _draw_game_over(self):
        """Helper that draws the GAME OVER message and restart prompt."""
        # Big title
        title = self.font_big.render("GAME OVER", True, COLOR_TEXT_BIG)
        # Center the title horizontally.
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2,
                                            WINDOW_HEIGHT // 2 - 30))
        self.screen.blit(title, title_rect)

        # Subtitle with final score
        subtitle = self.font_small.render(
            f"Final score: {int(self.score)}    Press R to restart, ESC to quit",
            True, COLOR_TEXT
        )
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2,
                                                  WINDOW_HEIGHT // 2 + 30))
        self.screen.blit(subtitle, subtitle_rect)

    def quit(self):
        """Cleanly shut down pygame and exit the program."""
        pygame.quit()
        sys.exit()

    def run(self):
        """The main game loop. Runs forever until the user quits.
        This loop is the single most important pattern in game programming -
        every game, from Pong to Skyrim, has some version of it."""
        while True:
            # `tick(TARGET_FPS)` does two things:
            #   1. Sleeps just long enough to keep us at TARGET_FPS.
            #   2. Returns how many milliseconds passed since the last call.
            # We divide by 1000 to convert to seconds for `delta_time`.
            delta_time = self.clock.tick(TARGET_FPS) / 1000.0

            self.handle_events()   # 1. Read input
            self.update(delta_time)  # 2. Update game state
            self.draw()              # 3. Draw new frame


# ==============================================================================
# PROGRAM ENTRY POINT
# ==============================================================================
# This `if __name__ == "__main__":` line is a Python idiom. It means
# "only run this code if the file is being run directly, not imported."
# It's good practice for any script you might later import elsewhere.
if __name__ == "__main__":
    Game().run()
