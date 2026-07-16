"""
================================================================================
                        SIMPLE ASTEROIDS GAME
================================================================================
A classic Asteroids clone written in Python using the Pygame library.

HOW TO PLAY:
    - LEFT / RIGHT arrow keys: Rotate your ship
    - UP arrow key:            Thrust forward
    - SPACEBAR:                Fire bullets
    - ESC:                     Quit the game
    - R:                       Restart after game over

HOW TO RUN:
    1. Make sure Python 3 is installed.
    2. Install pygame:  pip install pygame
    3. Run the game:    python asteroids.py

WHAT TO TRY MODIFYING (great for learning):
    - Change the CONSTANTS at the top of the file - they control everything!
    - Try changing colors, speeds, sizes, and counts to see what happens.
    - Each constant has a comment explaining what it does and suggestions.
================================================================================
"""

# We import the libraries we need.
# 'pygame' handles graphics, sound, and input.
# 'math' gives us trigonometry (sin, cos) for rotation and movement.
# 'random' lets us create unpredictable asteroid spawns and movements.
# 'sys' lets us cleanly exit the program.
import pygame
import math
import random
import sys


# ============================================================================
#                              CONSTANTS
# ============================================================================
# Constants are values that don't change while the game is running.
# By convention, we write them in ALL_CAPS to make them easy to spot.
# Tweaking these is the easiest way to experiment with the game!
# ============================================================================

# ---------- WINDOW SETTINGS ----------
# The size of the game window in pixels.
# Try 1280x720 for a bigger window, or 640x480 for a smaller one.
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700

# How many times per second the game updates and redraws.
# 60 is standard. Lower values (e.g. 30) feel choppy; higher values use more CPU.
FPS = 60

# The text shown in the window's title bar.
WINDOW_TITLE = "Asteroids"


# ---------- COLORS ----------
# Colors are tuples of (Red, Green, Blue), each from 0 (none) to 255 (full).
# Try changing these for a different look - e.g. green-on-black for a "Matrix" vibe.
COLOR_BACKGROUND = (10, 10, 30)        # Very dark blue (almost black) - the "space" color
COLOR_SHIP = (255, 255, 255)           # White - the player ship's outline
COLOR_THRUST = (255, 150, 50)          # Orange - the flame behind the ship when thrusting
COLOR_BULLET = (255, 255, 100)         # Yellow - the bullets you fire
COLOR_ASTEROID = (200, 200, 200)       # Light gray - asteroid outline
COLOR_TEXT = (255, 255, 255)           # White - score and message text
COLOR_GAME_OVER = (255, 80, 80)        # Red - the "GAME OVER" message
COLOR_STAR = (180, 180, 220)           # Pale blue-white - the background stars


# ---------- SHIP SETTINGS ----------
# The ship is drawn as a triangle. SHIP_SIZE is roughly the radius in pixels.
# Bigger = easier to see but easier to hit. Try 25 for a bigger ship.
SHIP_SIZE = 15

# How fast the ship rotates, in degrees per frame.
# Higher = quicker turns. Try 8 for snappy turning, 2 for sluggish.
SHIP_ROTATION_SPEED = 5

# How much speed the ship gains each frame while thrusting.
# Higher = more responsive but harder to control. Try 0.05 for slower acceleration.
SHIP_THRUST_POWER = 0.15

# Friction slows the ship down over time even without thrust.
# 1.0 = no friction (drifts forever). 0.99 = mild friction. 0.95 = heavy friction.
# Real space has no friction, but a tiny amount makes the game more playable.
SHIP_FRICTION = 0.995

# The maximum speed the ship can move at, in pixels per frame.
# Prevents the ship from becoming uncontrollably fast.
SHIP_MAX_SPEED = 8

# How many seconds the ship is invincible after respawning (flickers during this time).
# Gives the player time to react when a new life starts.
SHIP_INVINCIBILITY_TIME = 2.0

# How many lives the player starts with.
STARTING_LIVES = 3


# ---------- BULLET SETTINGS ----------
# How fast bullets travel, in pixels per frame.
BULLET_SPEED = 10

# How long each bullet exists, in seconds, before disappearing.
# Bullets that travel forever would clutter the screen.
BULLET_LIFETIME = 1.0

# The radius of each bullet, in pixels. Mostly affects how easy it is to see.
BULLET_RADIUS = 2

# Minimum time between shots, in seconds. Prevents holding spacebar from spamming.
# Lower = faster firing. Try 0.1 for a rapid-fire ship.
BULLET_COOLDOWN = 0.25


# ---------- ASTEROID SETTINGS ----------
# How many asteroids appear at the start of level 1.
# More asteroids = harder game. Each level adds one more.
STARTING_ASTEROID_COUNT = 4

# Asteroid sizes. We split big ones into smaller ones when shot.
# Larger numbers = bigger asteroids in pixels (radius).
ASTEROID_SIZE_LARGE = 40
ASTEROID_SIZE_MEDIUM = 25
ASTEROID_SIZE_SMALL = 15

# How fast asteroids drift across the screen, in pixels per frame.
# A random value between MIN and MAX is chosen for each asteroid.
ASTEROID_MIN_SPEED = 0.5
ASTEROID_MAX_SPEED = 2.0

# Smaller asteroids tend to be faster - this multiplies the speed when one splits.
# 1.5 means a medium asteroid is up to 1.5x faster than the large one it came from.
ASTEROID_SPEED_BOOST_ON_SPLIT = 1.3

# How "bumpy" the asteroid shape is. Each asteroid is drawn as a polygon
# with random radius variation. 0.0 = perfect circle, 0.5 = very jagged.
ASTEROID_JAGGEDNESS = 0.35

# Number of vertices (corners) on each asteroid polygon. More = smoother shape.
ASTEROID_VERTICES = 10


# ---------- SCORING ----------
# Points awarded for destroying each size of asteroid.
# Smaller asteroids are harder to hit, so they're worth more.
SCORE_LARGE_ASTEROID = 20
SCORE_MEDIUM_ASTEROID = 50
SCORE_SMALL_ASTEROID = 100

# Awarded an extra life every this-many points.
EXTRA_LIFE_SCORE = 1000


# ---------- BACKGROUND STARS ----------
# Decorative stars in the background. Pure cosmetics - won't affect gameplay.
STAR_COUNT = 80


# ============================================================================
#                              HELPER FUNCTIONS
# ============================================================================

def wrap_position(x, y):
    """
    Wraps coordinates around the screen edges (like Pac-Man tunnels).
    If something goes off the right side, it reappears on the left, etc.
    This is a hallmark of the original Asteroids game.

    Returns the new (x, y) position as a tuple.
    """
    # The modulo operator (%) gives the remainder of division.
    # For example, 950 % 900 = 50, which puts a ship at x=950 back at x=50.
    # Python's modulo also handles negative numbers nicely: -10 % 900 = 890.
    return (x % SCREEN_WIDTH, y % SCREEN_HEIGHT)


def distance_between(x1, y1, x2, y2):
    """
    Calculates the straight-line distance between two points using
    the Pythagorean theorem: distance = sqrt(dx^2 + dy^2).
    We use this to detect collisions (when distance < combined radius).
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


# ============================================================================
#                              GAME OBJECT CLASSES
# ============================================================================
# A "class" in Python is a blueprint for creating objects.
# Each class below represents one type of thing in the game (ship, bullet, etc.)
# ============================================================================

class Ship:
    """
    The player's spaceship. It can rotate, thrust, and shoot bullets.
    It wraps around screen edges like all other objects in the game.
    """

    def __init__(self, x, y):
        """
        Called when we create a new Ship. Sets up its starting state.
        'self' refers to this particular ship - each ship has its own values.
        """
        # Position of the ship's center on screen
        self.x = x
        self.y = y

        # Velocity (speed + direction) - how much x and y change per frame
        self.vx = 0
        self.vy = 0

        # The angle the ship is pointing, in degrees.
        # 0 = pointing right, 90 = down, 180 = left, 270 = up.
        # We start at 270 so the ship initially points UP.
        self.angle = 270

        # The ship's collision radius - used for hit detection
        self.radius = SHIP_SIZE

        # Whether the player is currently pressing the thrust key.
        # We track this so we can draw the engine flame.
        self.is_thrusting = False

        # Time remaining before this ship can shoot again, in seconds.
        # When > 0, the player must wait before firing.
        self.shoot_cooldown = 0

        # Time remaining where the ship is invincible (in seconds).
        # During this time, asteroids pass through the ship harmlessly.
        self.invincibility_timer = SHIP_INVINCIBILITY_TIME

    def update(self, dt, keys):
        """
        Updates the ship's state for one frame.
        'dt' is the time since last frame, in seconds (used for time-based things).
        'keys' is the dictionary of which keys are currently pressed.
        """
        # --- Handle rotation ---
        # If the player is holding LEFT, decrease the angle (rotate counterclockwise).
        if keys[pygame.K_LEFT]:
            self.angle -= SHIP_ROTATION_SPEED
        # If holding RIGHT, increase the angle (rotate clockwise).
        if keys[pygame.K_RIGHT]:
            self.angle += SHIP_ROTATION_SPEED

        # --- Handle thrust ---
        self.is_thrusting = keys[pygame.K_UP]
        if self.is_thrusting:
            # Convert the angle from degrees to radians (math functions need radians).
            angle_rad = math.radians(self.angle)
            # Add a bit of velocity in the direction the ship is pointing.
            # cos and sin convert an angle into x and y components.
            self.vx += math.cos(angle_rad) * SHIP_THRUST_POWER
            self.vy += math.sin(angle_rad) * SHIP_THRUST_POWER

        # --- Apply friction (slow the ship down slightly) ---
        # Multiplying by a number slightly less than 1 each frame
        # gradually reduces velocity toward zero.
        self.vx *= SHIP_FRICTION
        self.vy *= SHIP_FRICTION

        # --- Cap the maximum speed ---
        # Calculate current speed (magnitude of velocity vector)
        speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        if speed > SHIP_MAX_SPEED:
            # Scale velocity down so its length equals the max speed.
            self.vx = (self.vx / speed) * SHIP_MAX_SPEED
            self.vy = (self.vy / speed) * SHIP_MAX_SPEED

        # --- Update position based on velocity ---
        self.x += self.vx
        self.y += self.vy

        # --- Wrap around screen edges ---
        self.x, self.y = wrap_position(self.x, self.y)

        # --- Update timers ---
        # Subtract the time since the last frame from cooldown timers.
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invincibility_timer > 0:
            self.invincibility_timer -= dt

    def can_shoot(self):
        """Returns True if enough time has passed to shoot again."""
        return self.shoot_cooldown <= 0

    def shoot(self):
        """
        Creates a new bullet at the tip of the ship, traveling in the direction
        the ship is facing. Resets the shoot cooldown timer.
        Returns the new Bullet object.
        """
        # Reset cooldown so the player can't fire again immediately.
        self.shoot_cooldown = BULLET_COOLDOWN

        # Calculate the position of the ship's nose (where the bullet appears).
        angle_rad = math.radians(self.angle)
        nose_x = self.x + math.cos(angle_rad) * SHIP_SIZE
        nose_y = self.y + math.sin(angle_rad) * SHIP_SIZE

        # Calculate the bullet's velocity in the direction the ship is facing.
        bullet_vx = math.cos(angle_rad) * BULLET_SPEED
        bullet_vy = math.sin(angle_rad) * BULLET_SPEED

        return Bullet(nose_x, nose_y, bullet_vx, bullet_vy)

    def is_invincible(self):
        """Returns True if the ship is still in post-respawn invincibility."""
        return self.invincibility_timer > 0

    def draw(self, screen):
        """
        Draws the ship on the screen as a triangle.
        Also draws a flame behind the ship when thrusting.
        """
        # If invincible, flicker the ship by skipping drawing on alternating frames.
        # int(timer * 10) % 2 toggles between 0 and 1 at 5 times per second.
        if self.is_invincible() and int(self.invincibility_timer * 10) % 2 == 0:
            return  # Skip drawing this frame to create flicker effect

        # Convert angle to radians for math functions.
        angle_rad = math.radians(self.angle)

        # Calculate the three points of the triangle.
        # The "nose" is in the direction the ship is pointing.
        nose_x = self.x + math.cos(angle_rad) * SHIP_SIZE
        nose_y = self.y + math.sin(angle_rad) * SHIP_SIZE

        # The two "tail" points are 140 degrees from the nose on either side.
        # This makes a long, narrow triangle that looks ship-like.
        left_x = self.x + math.cos(angle_rad + math.radians(140)) * SHIP_SIZE
        left_y = self.y + math.sin(angle_rad + math.radians(140)) * SHIP_SIZE
        right_x = self.x + math.cos(angle_rad - math.radians(140)) * SHIP_SIZE
        right_y = self.y + math.sin(angle_rad - math.radians(140)) * SHIP_SIZE

        # Draw the ship as a triangle outline (width=2 means 2-pixel-thick line).
        points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(screen, COLOR_SHIP, points, 2)

        # If thrusting, draw a small flame behind the ship.
        if self.is_thrusting:
            # The flame is a small triangle that flickers in length.
            flame_size = SHIP_SIZE * 0.6 * random.uniform(0.5, 1.0)
            # Center of the back of the ship
            back_x = self.x - math.cos(angle_rad) * SHIP_SIZE * 0.5
            back_y = self.y - math.sin(angle_rad) * SHIP_SIZE * 0.5
            # Tip of the flame, behind the ship
            flame_tip_x = back_x - math.cos(angle_rad) * flame_size
            flame_tip_y = back_y - math.sin(angle_rad) * flame_size
            # Two side points of the flame
            flame_left_x = self.x + math.cos(angle_rad + math.radians(140)) * SHIP_SIZE * 0.6
            flame_left_y = self.y + math.sin(angle_rad + math.radians(140)) * SHIP_SIZE * 0.6
            flame_right_x = self.x + math.cos(angle_rad - math.radians(140)) * SHIP_SIZE * 0.6
            flame_right_y = self.y + math.sin(angle_rad - math.radians(140)) * SHIP_SIZE * 0.6
            flame_points = [(flame_tip_x, flame_tip_y),
                            (flame_left_x, flame_left_y),
                            (flame_right_x, flame_right_y)]
            pygame.draw.polygon(screen, COLOR_THRUST, flame_points)


class Bullet:
    """A small projectile fired by the ship. Travels in a straight line and disappears after a while."""

    def __init__(self, x, y, vx, vy):
        # Position
        self.x = x
        self.y = y
        # Velocity
        self.vx = vx
        self.vy = vy
        # How much longer this bullet exists, in seconds.
        self.lifetime = BULLET_LIFETIME
        # Used for collision detection.
        self.radius = BULLET_RADIUS

    def update(self, dt):
        """Move the bullet and reduce its lifetime."""
        self.x += self.vx
        self.y += self.vy
        # Wrap around screen edges, just like the ship.
        self.x, self.y = wrap_position(self.x, self.y)
        # Each frame, reduce the bullet's remaining lifetime.
        self.lifetime -= dt

    def is_alive(self):
        """Returns True if this bullet should still exist."""
        return self.lifetime > 0

    def draw(self, screen):
        """Draws the bullet as a small filled circle."""
        # pygame.draw.circle needs integer coordinates, so we convert with int().
        pygame.draw.circle(screen, COLOR_BULLET,
                           (int(self.x), int(self.y)), BULLET_RADIUS)


class Asteroid:
    """
    A drifting space rock. Comes in three sizes.
    When shot, large and medium asteroids split into two smaller ones.
    Small asteroids are simply destroyed.
    """

    def __init__(self, x, y, size):
        """
        Create an asteroid at (x, y) with the given size.
        'size' should be one of ASTEROID_SIZE_LARGE/MEDIUM/SMALL.
        """
        self.x = x
        self.y = y
        self.size = size  # The radius of the asteroid in pixels
        self.radius = size  # Used for collision detection

        # Pick a random direction and speed for this asteroid.
        # random.uniform gives us a random decimal between two values.
        angle = random.uniform(0, 2 * math.pi)  # Random direction in radians
        speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # Generate a randomly bumpy polygon shape for this asteroid.
        # We store the shape as a list of (offset_x, offset_y) points relative
        # to the asteroid's center. We compute it once and reuse it.
        self.shape_offsets = []
        for i in range(ASTEROID_VERTICES):
            # Distribute vertices evenly around the circle (in radians).
            vertex_angle = (i / ASTEROID_VERTICES) * 2 * math.pi
            # Vary each vertex's distance from center to look "rocky".
            radius_variation = random.uniform(1 - ASTEROID_JAGGEDNESS,
                                              1 + ASTEROID_JAGGEDNESS)
            r = size * radius_variation
            self.shape_offsets.append((math.cos(vertex_angle) * r,
                                       math.sin(vertex_angle) * r))

    def update(self, dt):
        """Move the asteroid and wrap around screen edges."""
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen):
        """Draws the asteroid as a polygon outline."""
        # Compute the absolute screen coordinates of each vertex.
        points = [(self.x + ox, self.y + oy) for (ox, oy) in self.shape_offsets]
        # Draw the outline (width=2 for a clean look).
        pygame.draw.polygon(screen, COLOR_ASTEROID, points, 2)

    def split(self):
        """
        Returns a list of new asteroids created when this one is destroyed.
        Large -> 2 medium, Medium -> 2 small, Small -> nothing (empty list).
        """
        # If it's already small, nothing comes out of it.
        if self.size <= ASTEROID_SIZE_SMALL:
            return []

        # Otherwise, the next size down...
        if self.size >= ASTEROID_SIZE_LARGE:
            new_size = ASTEROID_SIZE_MEDIUM
        else:
            new_size = ASTEROID_SIZE_SMALL

        # Create two new asteroids of the smaller size.
        new_asteroids = []
        for _ in range(2):
            new_asteroid = Asteroid(self.x, self.y, new_size)
            # Speed up the children a bit to make smaller pieces feel zippier.
            new_asteroid.vx *= ASTEROID_SPEED_BOOST_ON_SPLIT
            new_asteroid.vy *= ASTEROID_SPEED_BOOST_ON_SPLIT
            new_asteroids.append(new_asteroid)

        return new_asteroids

    def points_value(self):
        """How many points are awarded for destroying this asteroid."""
        if self.size >= ASTEROID_SIZE_LARGE:
            return SCORE_LARGE_ASTEROID
        elif self.size >= ASTEROID_SIZE_MEDIUM:
            return SCORE_MEDIUM_ASTEROID
        else:
            return SCORE_SMALL_ASTEROID


# ============================================================================
#                              THE MAIN GAME
# ============================================================================

class Game:
    """
    Manages everything: the player ship, asteroids, bullets, score, lives,
    and the overall game state (playing vs. game over).
    """

    def __init__(self):
        """Set up the game window and the initial state."""
        # Initialize all of pygame's subsystems (graphics, input, etc.)
        pygame.init()

        # Create the main game window.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)

        # The Clock helps us keep a steady frame rate.
        self.clock = pygame.time.Clock()

        # Pygame's font system, for drawing text on screen.
        # 'None' means use the default system font.
        self.font_small = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 72)

        # Generate a fixed pattern of background "stars" for atmosphere.
        # Each star is just a (x, y, brightness) tuple.
        self.stars = []
        for _ in range(STAR_COUNT):
            sx = random.randint(0, SCREEN_WIDTH - 1)
            sy = random.randint(0, SCREEN_HEIGHT - 1)
            brightness = random.randint(80, 255)
            self.stars.append((sx, sy, brightness))

        # Set up the actual game (ship, asteroids, score, etc.)
        self.reset_game()

    def reset_game(self):
        """Resets everything to a fresh new game state. Called at start and on restart."""
        # Place the ship in the center of the screen.
        self.ship = Ship(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        # Lists of currently-existing bullets and asteroids.
        # We add and remove from these as the game progresses.
        self.bullets = []
        self.asteroids = []

        # Game state values.
        self.score = 0
        self.lives = STARTING_LIVES
        self.level = 1
        self.game_over = False

        # Tracks at what score the next extra life is awarded.
        self.next_extra_life_score = EXTRA_LIFE_SCORE

        # Spawn the asteroids for level 1.
        self.spawn_level_asteroids()

    def spawn_level_asteroids(self):
        """
        Creates the asteroids for the current level.
        Each level has one more asteroid than the last.
        Asteroids spawn at the edges (away from the ship) so the player has time to react.
        """
        count = STARTING_ASTEROID_COUNT + (self.level - 1)

        for _ in range(count):
            # Try to find a position that's not too close to the ship.
            # We'll pick random spots and accept the first one that's far enough away.
            while True:
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                # Check the distance to the ship's current position.
                if distance_between(x, y, self.ship.x, self.ship.y) > 150:
                    # Far enough! Use this spot.
                    break

            # Create a large asteroid at this position.
            self.asteroids.append(Asteroid(x, y, ASTEROID_SIZE_LARGE))

    def handle_input(self, dt):
        """
        Processes one-shot inputs (key presses that should fire once, like shooting)
        and reads continuous keys via pygame.key.get_pressed.
        Returns False if the game should quit; True otherwise.
        """
        # Loop through all events that have happened since the last frame.
        for event in pygame.event.get():
            # The user clicked the window's close button.
            if event.type == pygame.QUIT:
                return False

            # The user pressed a key (this fires once per press).
            if event.type == pygame.KEYDOWN:
                # ESC quits the game.
                if event.key == pygame.K_ESCAPE:
                    return False

                # SPACE shoots a bullet (only if game is going and ship can shoot).
                if event.key == pygame.K_SPACE and not self.game_over:
                    if self.ship.can_shoot():
                        self.bullets.append(self.ship.shoot())

                # R restarts the game when game over.
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()

        return True  # Keep playing

    def update(self, dt):
        """Update all game objects for one frame."""
        # Don't update anything if the game is over.
        if self.game_over:
            return

        # Get a snapshot of all keys currently pressed.
        keys = pygame.key.get_pressed()

        # Update the ship's position, rotation, etc.
        self.ship.update(dt, keys)

        # Update all bullets, then remove the dead ones.
        for bullet in self.bullets:
            bullet.update(dt)
        # Keep only bullets that are still "alive".
        # This is called a list comprehension - a concise way to filter a list.
        self.bullets = [b for b in self.bullets if b.is_alive()]

        # Update all asteroids.
        for asteroid in self.asteroids:
            asteroid.update(dt)

        # Check for things hitting other things.
        self.check_collisions()

        # If all asteroids are destroyed, advance to the next level.
        if len(self.asteroids) == 0:
            self.level += 1
            # Reset the ship to the center, with brief invincibility.
            self.ship = Ship(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.spawn_level_asteroids()

    def check_collisions(self):
        """Detects bullet-vs-asteroid and ship-vs-asteroid collisions."""

        # --- Bullets vs. asteroids ---
        # We make new lists for what survives, then replace the originals.
        # This is safer than removing things from a list while we loop over it.
        surviving_bullets = []
        surviving_asteroids = list(self.asteroids)  # Start with all asteroids
        new_asteroids_from_splits = []

        for bullet in self.bullets:
            bullet_hit_something = False

            # Check this bullet against each asteroid.
            for asteroid in surviving_asteroids[:]:  # [:] makes a copy of the list to iterate
                if distance_between(bullet.x, bullet.y, asteroid.x, asteroid.y) < asteroid.radius:
                    # Collision! Score points.
                    self.score += asteroid.points_value()

                    # Maybe split the asteroid into smaller pieces.
                    new_asteroids_from_splits.extend(asteroid.split())

                    # Remove the destroyed asteroid.
                    surviving_asteroids.remove(asteroid)
                    bullet_hit_something = True

                    # Check for extra-life threshold.
                    if self.score >= self.next_extra_life_score:
                        self.lives += 1
                        self.next_extra_life_score += EXTRA_LIFE_SCORE

                    break  # This bullet is gone, no need to check more asteroids.

            # Keep this bullet only if it didn't hit anything.
            if not bullet_hit_something:
                surviving_bullets.append(bullet)

        # Update our master lists with the survivors and any new asteroid pieces.
        self.bullets = surviving_bullets
        self.asteroids = surviving_asteroids + new_asteroids_from_splits

        # --- Ship vs. asteroids ---
        # Skip if the ship is invincible (just respawned).
        if not self.ship.is_invincible():
            for asteroid in self.asteroids:
                if distance_between(self.ship.x, self.ship.y,
                                    asteroid.x, asteroid.y) < asteroid.radius + self.ship.radius:
                    # The ship was hit!
                    self.lives -= 1
                    if self.lives <= 0:
                        # No lives left - game over.
                        self.game_over = True
                    else:
                        # Respawn the ship in the center with brief invincibility.
                        self.ship = Ship(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                    break  # No point checking more asteroids this frame.

    def draw(self):
        """Draw everything to the screen."""
        # Fill the screen with the background color (clears the previous frame).
        self.screen.fill(COLOR_BACKGROUND)

        # Draw background stars first so they appear behind everything else.
        for (sx, sy, brightness) in self.stars:
            color = (brightness, brightness, min(255, brightness + 40))
            self.screen.set_at((sx, sy), color)  # set_at colors a single pixel

        # Draw asteroids.
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)

        # Draw bullets.
        for bullet in self.bullets:
            bullet.draw(self.screen)

        # Draw the ship (only if the game isn't over).
        if not self.game_over:
            self.ship.draw(self.screen)

        # Draw the heads-up display: score, lives, level.
        self.draw_hud()

        # Draw the "GAME OVER" overlay if needed.
        if self.game_over:
            self.draw_game_over()

        # All drawing happens to a hidden buffer; this swaps it to be visible.
        # This prevents flickering during drawing.
        pygame.display.flip()

    def draw_hud(self):
        """Draws the score, lives, and level info at the top of the screen."""
        # Render text into an image, then blit (copy) it to the screen.
        score_text = self.font_small.render(f"Score: {self.score}", True, COLOR_TEXT)
        self.screen.blit(score_text, (15, 10))

        lives_text = self.font_small.render(f"Lives: {self.lives}", True, COLOR_TEXT)
        self.screen.blit(lives_text, (15, 40))

        level_text = self.font_small.render(f"Level: {self.level}", True, COLOR_TEXT)
        # Right-align level text by measuring it first.
        level_rect = level_text.get_rect()
        level_rect.topright = (SCREEN_WIDTH - 15, 10)
        self.screen.blit(level_text, level_rect)

    def draw_game_over(self):
        """Draws the GAME OVER message and restart prompt."""
        # Big red "GAME OVER" text.
        msg = self.font_large.render("GAME OVER", True, COLOR_GAME_OVER)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(msg, msg_rect)

        # Smaller restart prompt.
        prompt = self.font_small.render("Press R to restart, ESC to quit",
                                        True, COLOR_TEXT)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(prompt, prompt_rect)

        # Final score.
        final = self.font_small.render(f"Final Score: {self.score}",
                                       True, COLOR_TEXT)
        final_rect = final.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(final, final_rect)

    def run(self):
        """The main game loop. Runs until the player quits."""
        running = True
        while running:
            # Tick the clock and get the time since the last frame in seconds.
            # Dividing milliseconds by 1000 gives us seconds.
            dt = self.clock.tick(FPS) / 1000.0

            # Process input (keyboard, window-close, etc.)
            running = self.handle_input(dt)

            # Update game logic (movement, collisions, etc.)
            self.update(dt)

            # Draw everything to the screen.
            self.draw()

        # When the loop ends, clean up pygame and exit.
        pygame.quit()
        sys.exit()


# ============================================================================
#                              ENTRY POINT
# ============================================================================
# This is where Python starts running when you execute this file.
# The 'if __name__ == "__main__":' check means this code only runs when
# you run the file directly (not when it's imported by another file).
# ============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
