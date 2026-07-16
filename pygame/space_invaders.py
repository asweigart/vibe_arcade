"""
================================================================================
SPACE INVADERS - A Beginner-Friendly Pygame Implementation
================================================================================

A classic Space Invaders clone written in a single file for easy learning.
No external assets needed - all graphics are drawn using shapes and pixel art.

HOW TO PLAY:
    - LEFT/RIGHT arrow keys (or A/D): Move your ship
    - SPACEBAR: Shoot
    - P: Pause/unpause the game
    - R: Restart after game over
    - ESC: Quit the game

HOW TO RUN:
    1. Install Pygame:  pip install pygame
    2. Run the file:    python space_invaders.py

WHAT TO TWEAK FIRST (if you want to experiment):
    - PLAYER_SPEED        -> make your ship faster or slower
    - ALIEN_SHOOT_CHANCE  -> make the game easier or harder
    - ALIEN_ROWS / ALIEN_COLS -> change how many enemies appear
    - Any of the COLOR_*  -> change the look of the game
================================================================================
"""

import pygame   # The game library that handles graphics, sound, and input
import random   # Used to make the aliens shoot at random times
import sys      # Used to cleanly exit the program

# ==============================================================================
# SECTION 1: CONSTANTS - All the "tunable knobs" of the game live here.
# ==============================================================================
# A "constant" is a value we set once and don't change while the game runs.
# Putting them all at the top makes it easy to experiment with different values.
# Try changing a number, save the file, and run again to see what happens!
# ==============================================================================

# ----- Window / Screen Settings -----------------------------------------------
SCREEN_WIDTH  = 800   # Width of the game window in pixels. Try 1024 for a wider view.
SCREEN_HEIGHT = 600   # Height of the game window in pixels. Try 768 for a taller view.
FPS           = 60    # Frames per second. 60 is smooth; lower values make it choppy.
WINDOW_TITLE  = "Space Invaders - Pygame Edition"

# ----- Colors -----------------------------------------------------------------
# Colors in pygame are tuples of (Red, Green, Blue), each from 0 (none) to 255 (max).
# Try mixing your own! For example, (255, 0, 255) is bright magenta.
COLOR_BLACK   = (  0,   0,   0)   # Background color of space
COLOR_WHITE   = (255, 255, 255)   # Used for text and stars
COLOR_GREEN   = (  0, 255,   0)   # Player ship color
COLOR_RED     = (255,  50,  50)   # Player bullets and "danger" text
COLOR_YELLOW  = (255, 255,   0)   # Alien bullets - very visible against black
COLOR_CYAN    = (  0, 255, 255)   # Front row of aliens (worth more points)
COLOR_MAGENTA = (255,   0, 255)   # Middle rows of aliens
COLOR_ORANGE  = (255, 165,   0)   # Back rows of aliens (worth fewer points)
COLOR_GRAY    = (100, 100, 100)   # Used for the bottom border line
COLOR_UI_TEXT = (200, 200, 200)   # Soft white for score / lives display

# ----- Player Settings --------------------------------------------------------
PLAYER_WIDTH      = 50    # How wide your ship is in pixels.
PLAYER_HEIGHT     = 30    # How tall your ship is in pixels.
PLAYER_SPEED      = 6     # How many pixels the ship moves each frame. Higher = faster.
PLAYER_START_LIVES = 3    # How many lives you start with. Try 5 for an easier game.
PLAYER_Y_OFFSET   = 50    # Distance from bottom of screen to player. Larger = higher up.
PLAYER_BULLET_COOLDOWN = 350  # Milliseconds between shots. Smaller = faster shooting.

# ----- Bullet Settings --------------------------------------------------------
BULLET_WIDTH        = 4    # How wide bullets are.
BULLET_HEIGHT       = 12   # How tall bullets are.
PLAYER_BULLET_SPEED = 9    # How fast YOUR bullets travel up the screen.
ALIEN_BULLET_SPEED  = 5    # How fast alien bullets travel down. Higher = harder.

# ----- Alien Settings ---------------------------------------------------------
ALIEN_ROWS        = 5     # Number of rows of aliens. Try 3 for fewer, 7 for more.
ALIEN_COLS        = 11    # Number of columns of aliens. Classic value is 11.
ALIEN_WIDTH       = 36    # How wide each alien is.
ALIEN_HEIGHT      = 26    # How tall each alien is.
ALIEN_H_SPACING   = 14    # Horizontal space between aliens.
ALIEN_V_SPACING   = 12    # Vertical space between aliens.
ALIEN_START_X     = 60    # Where the alien grid starts from the left edge.
ALIEN_START_Y     = 80    # Where the alien grid starts from the top.
ALIEN_BASE_SPEED  = 1     # How fast aliens move sideways (in pixels per "step").
ALIEN_DROP_DISTANCE = 18  # How far aliens drop when they hit a wall. Higher = quicker game over.
ALIEN_MOVE_INTERVAL_START = 600  # Milliseconds between alien moves at start. Smaller = faster.
ALIEN_MOVE_INTERVAL_MIN   = 60   # Fastest speed aliens can ever move (don't go below ~30).
ALIEN_SPEEDUP_FACTOR = 0.93  # Each kill multiplies the interval by this. Smaller = ramps up faster.
ALIEN_SHOOT_CHANCE  = 0.002  # Chance per frame each alien shoots. 0.005 = harder, 0.001 = easier.
ALIEN_MAX_BULLETS   = 4    # Max alien bullets on screen at once. Higher = chaos!

# ----- Scoring ----------------------------------------------------------------
# Different rows are worth different amounts of points (like the original game).
# Front row (bottom) = closest to player = worth the LEAST.
# Back row (top) = furthest = worth the MOST (harder to reach).
ALIEN_POINTS_BY_ROW = [40, 30, 20, 10, 10]  # Index 0 = top row. Add more values if you increase ALIEN_ROWS!

# ----- Star Field (background decoration) -------------------------------------
NUM_STARS = 80   # How many stars twinkle in the background. 0 disables them.

# ----- Fonts ------------------------------------------------------------------
FONT_SIZE_LARGE = 64    # Used for "GAME OVER" and "YOU WIN" messages.
FONT_SIZE_MEDIUM = 32   # Used for instructions on the start/end screens.
FONT_SIZE_SMALL = 22    # Used for score and lives display.


# ==============================================================================
# SECTION 2: PIXEL ART - Drawing aliens and the player without image files.
# ==============================================================================
# We define each sprite as a grid of 0s and 1s.
# A "1" means draw a colored pixel; a "0" means leave it transparent.
# We then blow up each cell into a small block of pixels on the screen.
#
# To design your own, just edit the strings - keep all rows the same length!
# ==============================================================================

# Player ship - a classic cannon/spaceship shape (11 wide x 7 tall)
PLAYER_SHAPE = [
    "00000100000",
    "00001110000",
    "00001110000",
    "01111111110",
    "11111111111",
    "11111111111",
    "11011111011",
]

# Alien type 1 - "squid" style, used for top row. (11 wide x 8 tall)
ALIEN_SHAPE_1 = [
    "00011111000",
    "01111111110",
    "11111111111",
    "11100111011",
    "11111111111",
    "00111011100",
    "01100000110",
    "00011011000",
]

# Alien type 2 - "crab" style, used for middle rows.
ALIEN_SHAPE_2 = [
    "00100000100",
    "10010001001",
    "10111111101",
    "11101110111",
    "11111111111",
    "01111111110",
    "00100000100",
    "01000000010",
]

# Alien type 3 - "octopus" style, used for bottom rows.
ALIEN_SHAPE_3 = [
    "00001110000",
    "00111111100",
    "01111111110",
    "11100111011",
    "11111111111",
    "00010001000",
    "00101110100",
    "01010001010",
]


# ==============================================================================
# SECTION 3: HELPER FUNCTIONS
# ==============================================================================

def draw_pixel_shape(surface, shape, top_left_x, top_left_y, pixel_size, color):
    """
    Draws a pixel-art shape onto the given surface.

    'shape' is a list of strings of '0' and '1'.
    Each '1' becomes a square of size 'pixel_size' x 'pixel_size' in 'color'.
    'top_left_x' and 'top_left_y' are where the shape starts being drawn.

    This is what lets us create graphics without loading any image files!
    """
    for row_index, row in enumerate(shape):
        for col_index, pixel in enumerate(row):
            if pixel == "1":
                # pygame.Rect(x, y, width, height) defines a rectangle.
                rect = pygame.Rect(
                    top_left_x + col_index * pixel_size,
                    top_left_y + row_index * pixel_size,
                    pixel_size,
                    pixel_size,
                )
                pygame.draw.rect(surface, color, rect)


def get_alien_color_for_row(row_index):
    """
    Returns a color depending on which row of aliens we're drawing.
    The top row uses one color, middle rows another, bottom rows another.
    Edit this to change how the alien fleet looks.
    """
    if row_index == 0:
        return COLOR_CYAN          # Top row - hardest to hit, most valuable
    elif row_index in (1, 2):
        return COLOR_MAGENTA       # Middle rows
    else:
        return COLOR_ORANGE        # Bottom rows


def get_alien_shape_for_row(row_index):
    """
    Returns one of the three alien designs depending on the row number.
    Mixing shapes makes the fleet look more interesting.
    """
    if row_index == 0:
        return ALIEN_SHAPE_1
    elif row_index in (1, 2):
        return ALIEN_SHAPE_2
    else:
        return ALIEN_SHAPE_3


# ==============================================================================
# SECTION 4: GAME OBJECT CLASSES
# ==============================================================================
# In Python, a "class" is a blueprint for creating objects.
# Each Player, Alien, and Bullet in the game is an "instance" of its class.
# ==============================================================================

class Player:
    """The player's ship at the bottom of the screen."""

    def __init__(self):
        # Starting position: horizontally centered, near the bottom
        self.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self.y = SCREEN_HEIGHT - PLAYER_Y_OFFSET - PLAYER_HEIGHT
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.lives = PLAYER_START_LIVES
        self.last_shot_time = 0  # Used to enforce shooting cooldown

    def get_rect(self):
        """Returns a pygame Rect representing this object's bounds.
        We use this for collision detection (checking if things touch)."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, keys_pressed):
        """Update the player's position based on which keys are being held down.
        'keys_pressed' is a list of all keys' current state from pygame."""
        # Allow both arrow keys AND WASD-style controls
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.x -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.x += PLAYER_SPEED

        # Keep the player on screen - don't let them walk off the edges.
        if self.x < 0:
            self.x = 0
        if self.x + self.width > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width

    def can_shoot(self, current_time_ms):
        """Returns True if enough time has passed since the last shot."""
        return current_time_ms - self.last_shot_time >= PLAYER_BULLET_COOLDOWN

    def draw(self, surface):
        """Draws the player ship at its current position."""
        # We use a "pixel size" of 4 to scale up the small pixel-art shape.
        # Calculate so the design fits nicely inside the player's hitbox.
        pixel_size = PLAYER_WIDTH // len(PLAYER_SHAPE[0])
        draw_pixel_shape(surface, PLAYER_SHAPE, self.x, self.y, pixel_size, COLOR_GREEN)


class Alien:
    """A single alien enemy in the invading fleet."""

    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.row = row                                 # Which row (used for color/score)
        self.width = ALIEN_WIDTH
        self.height = ALIEN_HEIGHT
        self.alive = True                              # Becomes False when shot
        self.points = ALIEN_POINTS_BY_ROW[row]         # How many points killing this alien gives
        self.color = get_alien_color_for_row(row)
        self.shape = get_alien_shape_for_row(row)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        if not self.alive:
            return  # Don't draw dead aliens
        pixel_size = ALIEN_WIDTH // len(self.shape[0])
        draw_pixel_shape(surface, self.shape, self.x, self.y, pixel_size, self.color)


class Bullet:
    """A bullet, either fired by the player or by an alien.
    The 'direction' is -1 if going up (player shot) or +1 if going down (alien shot)."""

    def __init__(self, x, y, direction, speed, color):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.color = color
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.active = True   # Set to False when bullet leaves the screen or hits something

    def update(self):
        """Move the bullet by its speed in its direction."""
        self.y += self.speed * self.direction
        # Mark for removal if it has flown off the screen
        if self.y < 0 or self.y > SCREEN_HEIGHT:
            self.active = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.get_rect())


# ==============================================================================
# SECTION 5: THE MAIN GAME CLASS
# ==============================================================================
# This class holds the entire game state and the main game loop.
# Putting everything in a class makes it easy to "reset" by creating a new one.
# ==============================================================================

class SpaceInvadersGame:
    def __init__(self):
        # Initialize pygame - this must be called before using most pygame features
        pygame.init()

        # Create the window where everything will be drawn
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)

        # The Clock object helps us control how fast the game runs
        self.clock = pygame.time.Clock()

        # Set up fonts. None means use the default system font.
        self.font_large  = pygame.font.SysFont(None, FONT_SIZE_LARGE)
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_small  = pygame.font.SysFont(None, FONT_SIZE_SMALL)

        # Generate twinkling background stars - just random (x, y) positions
        self.stars = [
            (random.randint(0, SCREEN_WIDTH - 1), random.randint(0, SCREEN_HEIGHT - 1))
            for _ in range(NUM_STARS)
        ]

        # Set up the actual game state (player, aliens, score, etc.)
        self.reset_game()

    def reset_game(self):
        """Sets all game state back to the starting position.
        Called at startup AND when the player presses R after dying."""
        self.player = Player()
        self.aliens = self.create_alien_fleet()
        self.player_bullets = []        # List of bullets the player has fired
        self.alien_bullets = []         # List of bullets the aliens have fired
        self.score = 0
        self.alien_direction = 1        # 1 = moving right, -1 = moving left
        self.alien_move_interval = ALIEN_MOVE_INTERVAL_START
        self.last_alien_move_time = pygame.time.get_ticks()
        self.game_over = False
        self.game_won = False
        self.paused = False

    def create_alien_fleet(self):
        """Builds the grid of aliens at the start of the game."""
        aliens = []
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                # Calculate this alien's screen position based on its row/col
                x = ALIEN_START_X + col * (ALIEN_WIDTH + ALIEN_H_SPACING)
                y = ALIEN_START_Y + row * (ALIEN_HEIGHT + ALIEN_V_SPACING)
                aliens.append(Alien(x, y, row))
        return aliens

    # --------------------------------------------------------------------------
    # Input handling
    # --------------------------------------------------------------------------
    def handle_events(self):
        """Process all input events: keypresses, window close, etc.
        Pygame puts every input into an 'event queue' that we drain each frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the X to close the window
                self.quit_game()

            elif event.type == pygame.KEYDOWN:
                # A key was just pressed (this fires once per press)
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
                elif event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_SPACE and not self.game_over and not self.paused:
                    self.try_player_shoot()

    def try_player_shoot(self):
        """Fires a player bullet if the cooldown has elapsed."""
        current_time = pygame.time.get_ticks()
        if self.player.can_shoot(current_time):
            # Spawn the bullet at the top-center of the player ship
            bullet_x = self.player.x + self.player.width // 2 - BULLET_WIDTH // 2
            bullet_y = self.player.y
            new_bullet = Bullet(
                x=bullet_x,
                y=bullet_y,
                direction=-1,                  # -1 means upward
                speed=PLAYER_BULLET_SPEED,
                color=COLOR_RED,
            )
            self.player_bullets.append(new_bullet)
            self.player.last_shot_time = current_time

    # --------------------------------------------------------------------------
    # Per-frame updates
    # --------------------------------------------------------------------------
    def update(self):
        """Advance the game state by one frame.
        This is where movement, shooting, and collisions happen."""
        if self.paused or self.game_over:
            return  # Frozen - nothing moves

        # Player movement: read keys directly (so holding works smoothly)
        keys = pygame.key.get_pressed()
        self.player.move(keys)

        # Update bullets
        self.update_bullets()

        # Update aliens (they move on a timer, not every frame)
        self.update_aliens()

        # Random alien shooting
        self.maybe_alien_shoot()

        # Check for collisions between bullets and ships
        self.check_collisions()

        # Check whether the game has ended (won or lost)
        self.check_end_conditions()

    def update_bullets(self):
        """Move all bullets and remove any that have flown off screen."""
        for bullet in self.player_bullets:
            bullet.update()
        for bullet in self.alien_bullets:
            bullet.update()

        # 'List comprehension' that keeps only the bullets still active.
        # This is Python shorthand for "make a new list of items that pass a test".
        self.player_bullets = [b for b in self.player_bullets if b.active]
        self.alien_bullets  = [b for b in self.alien_bullets  if b.active]

    def update_aliens(self):
        """Move the alien fleet sideways. When they hit a wall, they drop down
        and reverse direction - the classic Space Invaders behavior."""
        current_time = pygame.time.get_ticks()
        # Only move if enough time has passed since the last move
        if current_time - self.last_alien_move_time < self.alien_move_interval:
            return
        self.last_alien_move_time = current_time

        # Find the leftmost and rightmost living aliens to test against the walls.
        living_aliens = [a for a in self.aliens if a.alive]
        if not living_aliens:
            return  # No aliens left to move

        leftmost  = min(a.x for a in living_aliens)
        rightmost = max(a.x + a.width for a in living_aliens)

        # Decide whether the fleet should change direction and drop.
        hit_right_wall = self.alien_direction == 1  and rightmost + ALIEN_BASE_SPEED >= SCREEN_WIDTH
        hit_left_wall  = self.alien_direction == -1 and leftmost  - ALIEN_BASE_SPEED <= 0

        if hit_right_wall or hit_left_wall:
            # Flip horizontal direction and drop the entire fleet down a step.
            self.alien_direction *= -1
            for alien in living_aliens:
                alien.y += ALIEN_DROP_DISTANCE
        else:
            # Normal sideways movement
            for alien in living_aliens:
                alien.x += ALIEN_BASE_SPEED * self.alien_direction

    def maybe_alien_shoot(self):
        """Each frame, each alien has a small chance to shoot.
        We also cap how many alien bullets can be on screen at once."""
        if len(self.alien_bullets) >= ALIEN_MAX_BULLETS:
            return

        for alien in self.aliens:
            if not alien.alive:
                continue
            # random.random() returns a number between 0.0 and 1.0
            if random.random() < ALIEN_SHOOT_CHANCE:
                bullet_x = alien.x + alien.width // 2 - BULLET_WIDTH // 2
                bullet_y = alien.y + alien.height
                new_bullet = Bullet(
                    x=bullet_x,
                    y=bullet_y,
                    direction=1,                # +1 means downward
                    speed=ALIEN_BULLET_SPEED,
                    color=COLOR_YELLOW,
                )
                self.alien_bullets.append(new_bullet)
                # Stop after one shot per frame to avoid bullet floods
                if len(self.alien_bullets) >= ALIEN_MAX_BULLETS:
                    break

    def check_collisions(self):
        """Test every bullet against every potential target."""
        # Player bullets hitting aliens
        for bullet in self.player_bullets:
            if not bullet.active:
                continue
            bullet_rect = bullet.get_rect()
            for alien in self.aliens:
                if alien.alive and bullet_rect.colliderect(alien.get_rect()):
                    alien.alive = False
                    bullet.active = False
                    self.score += alien.points
                    # Each kill speeds up the fleet a little - tension grows!
                    self.alien_move_interval = max(
                        ALIEN_MOVE_INTERVAL_MIN,
                        int(self.alien_move_interval * ALIEN_SPEEDUP_FACTOR),
                    )
                    break  # One bullet can only kill one alien

        # Alien bullets hitting the player
        player_rect = self.player.get_rect()
        for bullet in self.alien_bullets:
            if bullet.active and bullet.get_rect().colliderect(player_rect):
                bullet.active = False
                self.player.lives -= 1
                # Brief invulnerability could go here. For simplicity, we just
                # clear all alien bullets so the player isn't instantly hit again.
                self.alien_bullets = []
                break

    def check_end_conditions(self):
        """Check whether the game has been won or lost."""
        # Lose condition 1: player has run out of lives
        if self.player.lives <= 0:
            self.game_over = True
            self.game_won = False
            return

        # Lose condition 2: aliens have reached the player's level
        for alien in self.aliens:
            if alien.alive and alien.y + alien.height >= self.player.y:
                self.game_over = True
                self.game_won = False
                return

        # Win condition: all aliens dead!
        if not any(alien.alive for alien in self.aliens):
            self.game_over = True
            self.game_won = True

    # --------------------------------------------------------------------------
    # Drawing
    # --------------------------------------------------------------------------
    def draw(self):
        """Draw everything for the current frame."""
        # 1. Clear the screen by painting it black
        self.screen.fill(COLOR_BLACK)

        # 2. Draw the background stars
        for star_x, star_y in self.stars:
            self.screen.set_at((star_x, star_y), COLOR_WHITE)

        # 3. Draw a thin gray line near the bottom for visual flair
        line_y = SCREEN_HEIGHT - PLAYER_Y_OFFSET // 2
        pygame.draw.line(self.screen, COLOR_GRAY, (0, line_y), (SCREEN_WIDTH, line_y), 1)

        # 4. Draw all game objects
        self.player.draw(self.screen)
        for alien in self.aliens:
            alien.draw(self.screen)
        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.alien_bullets:
            bullet.draw(self.screen)

        # 5. Draw the heads-up display (score, lives) on top of everything
        self.draw_hud()

        # 6. Draw any overlays (paused / game over / you win)
        if self.paused:
            self.draw_centered_text("PAUSED", self.font_large, COLOR_WHITE, y_offset=-20)
            self.draw_centered_text("Press P to resume", self.font_medium, COLOR_UI_TEXT, y_offset=40)
        elif self.game_over:
            if self.game_won:
                self.draw_centered_text("YOU WIN!", self.font_large, COLOR_GREEN, y_offset=-40)
            else:
                self.draw_centered_text("GAME OVER", self.font_large, COLOR_RED, y_offset=-40)
            self.draw_centered_text(f"Final Score: {self.score}", self.font_medium, COLOR_WHITE, y_offset=20)
            self.draw_centered_text("Press R to restart  -  ESC to quit", self.font_medium, COLOR_UI_TEXT, y_offset=70)

        # 7. Actually show what we just drew (pygame uses 'double buffering')
        pygame.display.flip()

    def draw_hud(self):
        """Draws the score in the top-left and lives in the top-right."""
        score_surface = self.font_small.render(f"SCORE: {self.score}", True, COLOR_UI_TEXT)
        self.screen.blit(score_surface, (10, 10))

        lives_surface = self.font_small.render(f"LIVES: {self.player.lives}", True, COLOR_UI_TEXT)
        # Right-align by computing where it should start
        lives_x = SCREEN_WIDTH - lives_surface.get_width() - 10
        self.screen.blit(lives_surface, (lives_x, 10))

    def draw_centered_text(self, text, font, color, y_offset=0):
        """Draws a string centered on the screen.
        'y_offset' lets you nudge it up or down from the middle."""
        text_surface = font.render(text, True, color)
        x = SCREEN_WIDTH // 2 - text_surface.get_width() // 2
        y = SCREEN_HEIGHT // 2 - text_surface.get_height() // 2 + y_offset
        self.screen.blit(text_surface, (x, y))

    # --------------------------------------------------------------------------
    # Main loop and shutdown
    # --------------------------------------------------------------------------
    def run(self):
        """The heart of the game: the loop that runs until the player quits.
        Each iteration is one 'frame' - typically 1/60th of a second."""
        while True:
            self.handle_events()    # Read input
            self.update()           # Move things, check collisions
            self.draw()             # Draw the frame
            self.clock.tick(FPS)    # Wait so we run at the target FPS

    def quit_game(self):
        """Cleanly shut down pygame and exit the program."""
        pygame.quit()
        sys.exit()


# ==============================================================================
# SECTION 6: PROGRAM ENTRY POINT
# ==============================================================================
# This special block runs only when you execute this file directly.
# It won't run if someone imports this file from another script.
# ==============================================================================

if __name__ == "__main__":
    game = SpaceInvadersGame()
    game.run()
