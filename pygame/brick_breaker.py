"""
=============================================================================
BRICK BREAKER (a.k.a. Arkanoid) - A beginner-friendly Pygame example
=============================================================================

HOW TO RUN:
    1. Install Python 3.8+ if you don't have it already.
    2. Install pygame:    pip install pygame
    3. Run the game:      python brick_breaker.py

HOW TO PLAY:
    - Move the paddle with the LEFT and RIGHT arrow keys (or A / D).
    - Press SPACE to launch the ball when it is sitting on the paddle.
    - Break all the bricks to win the level.
    - Don't let the ball fall off the bottom of the screen!
    - Press R to restart after winning or losing.
    - Press ESC to quit.

WHAT THIS FILE TEACHES:
    - The basic Pygame "game loop" (events -> update -> draw -> repeat).
    - Using simple classes (Paddle, Ball, Brick) to organize game objects.
    - Collision detection with axis-aligned rectangles.
    - Drawing primitives (rectangles, circles, text) without any image files.
    - Using lots of named CONSTANTS so you can tweak the feel of the game
      without hunting through the code.

WHERE TO TWEAK THINGS:
    Almost every "magic number" lives in the CONSTANTS section near the top.
    Each constant has a comment explaining what it does and a suggestion for
    how changing it will affect gameplay. Try changing a few values!
=============================================================================
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
# `pygame` is the library that handles drawing, input, and timing.
# `sys` lets us cleanly exit the program.
# `random` is used to give the ball a slightly varied starting direction
# and to vary brick colors.
# `math` is used for some simple trigonometry when bouncing the ball off
# the paddle (so we can aim it based on where it hits).
import sys
import math
import random
import pygame


# =============================================================================
# CONSTANTS - tweak these to change how the game looks and feels!
# =============================================================================

# --- Window / display --------------------------------------------------------
# SCREEN_WIDTH and SCREEN_HEIGHT control the size of the game window in pixels.
# Try 1024x768 for a bigger window, or 600x800 for a tall, narrow playfield.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Window title shown in the title bar.
WINDOW_TITLE = "Brick Breaker"

# FPS = Frames Per Second. 60 is smooth and standard. Lowering this (e.g. 30)
# will make the whole game feel slower and choppier; raising it past 60 won't
# usually help unless your monitor refreshes faster.
FPS = 60


# --- Colors (R, G, B) tuples, each value 0-255 ------------------------------
# Feel free to redesign the palette here. Pygame uses RGB (red, green, blue).
COLOR_BACKGROUND = (15, 15, 30)        # Dark navy backdrop. Try (0, 0, 0) for black.
COLOR_PADDLE     = (230, 230, 230)     # Almost-white paddle.
COLOR_BALL       = (255, 220, 80)      # Yellow ball. Try (255, 80, 80) for red.
COLOR_TEXT       = (240, 240, 240)     # UI text color.
COLOR_TEXT_DIM   = (160, 160, 180)     # Subtler text (e.g. instructions).
COLOR_BORDER     = (60, 60, 90)        # Color used to outline things.

# Brick colors are picked from this list, one per row (top row = index 0).
# Add or remove tuples to change the rainbow stack.
BRICK_ROW_COLORS = [
    (231,  76,  60),   # red
    (230, 126,  34),   # orange
    (241, 196,  15),   # yellow
    ( 46, 204, 113),   # green
    ( 52, 152, 219),   # blue
    (155,  89, 182),   # purple
]


# --- Paddle ------------------------------------------------------------------
# Width controls how forgiving the game feels. A wider paddle is easier.
PADDLE_WIDTH = 110
PADDLE_HEIGHT = 16

# Distance from the bottom of the screen to the paddle.
# Increase to give yourself more reaction room above the bottom edge.
PADDLE_Y_OFFSET = 40

# How fast the paddle moves in pixels per frame. Higher = twitchier control.
PADDLE_SPEED = 9


# --- Ball --------------------------------------------------------------------
# Ball size in pixels (it's drawn as a circle with this radius).
BALL_RADIUS = 8

# Starting speed of the ball in pixels per frame. Try 4 for "easy", 8 for "hard".
BALL_INITIAL_SPEED = 6

# Maximum speed the ball can reach. The ball speeds up slightly each time it
# hits a brick, which keeps later bricks from feeling too easy.
BALL_MAX_SPEED = 12

# How much the ball speeds up per brick hit. Set to 0 for constant speed.
BALL_SPEED_INCREMENT = 0.05

# When the ball hits the paddle, we bounce it at an angle based on WHERE it
# hit the paddle (left edge -> sharp left, right edge -> sharp right, middle
# -> almost straight up). MAX_BOUNCE_ANGLE_DEG is how steep that angle can get.
# Smaller values (e.g. 45) make play more vertical; larger (e.g. 75) more wild.
MAX_BOUNCE_ANGLE_DEG = 60


# --- Bricks ------------------------------------------------------------------
# Number of brick rows and columns. More rows/cols = more bricks to break.
BRICK_ROWS = 6
BRICK_COLS = 10

# Pixel gap between adjacent bricks. 0 = bricks touch each other.
BRICK_PADDING = 4

# Margins from the edges of the screen to where the brick field starts.
BRICK_FIELD_LEFT_MARGIN = 40
BRICK_FIELD_RIGHT_MARGIN = 40
BRICK_FIELD_TOP_MARGIN = 80   # leaves room for the score bar at the top.

# Brick height in pixels. Brick width is calculated automatically from the
# screen width, the column count, and the margins so the rows fit perfectly.
BRICK_HEIGHT = 22


# --- Lives & scoring ---------------------------------------------------------
# Number of balls (lives) the player gets per game.
STARTING_LIVES = 3

# Points awarded per brick destroyed. Higher rows can be worth more if you
# customize this — see the Brick.points calculation in the Brick class.
POINTS_PER_BRICK = 10


# --- Fonts -------------------------------------------------------------------
# Pygame's default font is used so we don't need any font files.
FONT_NAME = None        # None = pygame's built-in default font.
HUD_FONT_SIZE = 22      # Score / lives text at the top of the screen.
BIG_FONT_SIZE = 56      # "YOU WIN" / "GAME OVER" text.
SMALL_FONT_SIZE = 20    # Hint text like "Press SPACE to launch".


# =============================================================================
# DERIVED VALUES - calculated from the constants above. You normally don't
# need to change these directly; change the constants and these will update.
# =============================================================================

# Total horizontal space available for the brick field.
_BRICK_FIELD_WIDTH = (
    SCREEN_WIDTH - BRICK_FIELD_LEFT_MARGIN - BRICK_FIELD_RIGHT_MARGIN
)

# Width of a single brick, accounting for the gaps between bricks.
BRICK_WIDTH = (
    _BRICK_FIELD_WIDTH - BRICK_PADDING * (BRICK_COLS - 1)
) // BRICK_COLS


# =============================================================================
# CLASSES - one for each kind of game object.
# =============================================================================

class Paddle:
    """The player-controlled paddle at the bottom of the screen."""

    def __init__(self):
        # We use a pygame.Rect to store position AND size together. Rects also
        # have helpful methods for collision detection (e.g. colliderect).
        self.rect = pygame.Rect(
            (SCREEN_WIDTH - PADDLE_WIDTH) // 2,            # centered horizontally
            SCREEN_HEIGHT - PADDLE_Y_OFFSET - PADDLE_HEIGHT,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        self.speed = PADDLE_SPEED

    def update(self, keys_pressed):
        """Move the paddle based on which keys are currently held down."""
        # `keys_pressed` is the dictionary returned by pygame.key.get_pressed().
        # Supporting both arrow keys and WASD is just a kindness to the player.
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.rect.x -= self.speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.rect.x += self.speed

        # Clamp the paddle so it can't go off the edges of the screen.
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def draw(self, surface):
        """Draw the paddle as a rounded rectangle for a slightly nicer look."""
        # The third argument (border_radius) rounds the corners. Set to 0 for
        # sharp corners, or a larger number for very round/pill-shaped paddles.
        pygame.draw.rect(surface, COLOR_PADDLE, self.rect, border_radius=8)


class Ball:
    """The bouncing ball."""

    def __init__(self, paddle):
        # We track the ball's position as floats (x, y) so we can move it by
        # fractional speeds. Pygame's Rect only stores integer coordinates,
        # which causes jittery motion if we used it directly.
        self.x = 0.0
        self.y = 0.0

        # Velocity components (pixels per frame).
        self.vx = 0.0
        self.vy = 0.0

        # Current speed magnitude (it grows as you hit bricks).
        self.speed = BALL_INITIAL_SPEED

        # When True, the ball sticks to the paddle and waits for SPACE.
        self.stuck_to_paddle = True

        # Reference to the paddle so we can sit on top of it before launch.
        self.paddle = paddle

        # Place the ball in its starting position.
        self.reset()

    def reset(self):
        """Put the ball back on top of the paddle, waiting to be launched."""
        self.stuck_to_paddle = True
        self.speed = BALL_INITIAL_SPEED
        # Sit centered on top of the paddle.
        self.x = self.paddle.rect.centerx
        self.y = self.paddle.rect.top - BALL_RADIUS - 1
        self.vx = 0.0
        self.vy = 0.0

    def launch(self):
        """Send the ball flying upward with a slight random angle."""
        if not self.stuck_to_paddle:
            return  # Already in flight; ignore.

        # Pick a random angle near "straight up" so launches aren't identical.
        # 0 degrees here = straight up, positive = right, negative = left.
        angle_deg = random.uniform(-30, 30)
        angle_rad = math.radians(angle_deg)
        self.vx = math.sin(angle_rad) * self.speed
        self.vy = -math.cos(angle_rad) * self.speed   # negative = upward
        self.stuck_to_paddle = False

    def update(self, paddle, bricks):
        """Move the ball and handle collisions. Returns points scored this frame."""
        scored = 0

        if self.stuck_to_paddle:
            # Glue the ball to the paddle until launch.
            self.x = paddle.rect.centerx
            self.y = paddle.rect.top - BALL_RADIUS - 1
            return scored

        # Move the ball.
        self.x += self.vx
        self.y += self.vy

        # --- Wall collisions ---
        # Left wall:
        if self.x - BALL_RADIUS < 0:
            self.x = BALL_RADIUS
            self.vx = -self.vx
        # Right wall:
        if self.x + BALL_RADIUS > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - BALL_RADIUS
            self.vx = -self.vx
        # Top wall:
        if self.y - BALL_RADIUS < 0:
            self.y = BALL_RADIUS
            self.vy = -self.vy
        # NOTE: We intentionally do NOT bounce off the bottom — falling off
        # the bottom is how you lose a life (handled in the main game loop).

        # --- Paddle collision ---
        # Build a small rect for the ball so we can use Pygame's collision check.
        ball_rect = self._rect()
        if ball_rect.colliderect(paddle.rect) and self.vy > 0:
            # Only bounce when traveling downward, so we don't get "stuck"
            # inside the paddle if a frame puts us slightly inside it.
            self._bounce_off_paddle(paddle)

        # --- Brick collisions ---
        # We loop through bricks and check the first one we collide with.
        # When we hit a brick, we figure out which side we hit so the bounce
        # looks correct (a ball hitting the side of a brick should reverse
        # horizontally, while one hitting the top/bottom should reverse vertically).
        for brick in bricks:
            if not brick.alive:
                continue
            if ball_rect.colliderect(brick.rect):
                self._bounce_off_brick(brick, ball_rect)
                brick.alive = False
                scored += brick.points

                # Slightly speed up the ball each brick hit, up to a cap.
                self.speed = min(self.speed + BALL_SPEED_INCREMENT, BALL_MAX_SPEED)
                self._renormalize_velocity()

                # Only handle one brick per frame to avoid weird double-bounces.
                break

        return scored

    def _bounce_off_paddle(self, paddle):
        """
        Bounce off the paddle with an angle determined by where the ball hit.
        Hitting the center sends the ball nearly straight up; hitting the
        edges sends it sharply sideways. This is the classic Arkanoid feel
        and gives the player real control over aiming.
        """
        # How far from the paddle's center did the ball land?
        # Range: -1.0 (left edge) ... 0.0 (center) ... +1.0 (right edge).
        offset = (self.x - paddle.rect.centerx) / (paddle.rect.width / 2)
        # Clamp in case the ball is slightly past the edge.
        offset = max(-1.0, min(1.0, offset))

        # Convert that offset into an angle.
        bounce_angle = math.radians(offset * MAX_BOUNCE_ANGLE_DEG)

        # Recompute velocity from the angle, keeping current speed.
        self.vx = math.sin(bounce_angle) * self.speed
        self.vy = -abs(math.cos(bounce_angle) * self.speed)  # always upward

        # Nudge the ball above the paddle so we don't re-collide next frame.
        self.y = paddle.rect.top - BALL_RADIUS - 1

    def _bounce_off_brick(self, brick, ball_rect):
        """
        Decide whether to reverse horizontal or vertical velocity based on
        which side of the brick we likely entered through. We compare how
        deep the ball overlaps along each axis; the smaller overlap is the
        side we entered from.
        """
        # Compute overlap on each axis.
        overlap_left   = ball_rect.right  - brick.rect.left    # entered from left
        overlap_right  = brick.rect.right - ball_rect.left     # entered from right
        overlap_top    = ball_rect.bottom - brick.rect.top     # entered from top
        overlap_bottom = brick.rect.bottom - ball_rect.top     # entered from bottom

        # The minimum overlap is the axis we just barely crossed -> bounce on it.
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left or min_overlap == overlap_right:
            self.vx = -self.vx
        else:
            self.vy = -self.vy

    def _renormalize_velocity(self):
        """Make sure the velocity vector has the right speed magnitude."""
        # When we change `self.speed`, the existing vx/vy don't automatically
        # get longer or shorter. We rescale them so |(vx, vy)| == self.speed.
        magnitude = math.hypot(self.vx, self.vy)
        if magnitude == 0:
            return  # Avoid dividing by zero.
        scale = self.speed / magnitude
        self.vx *= scale
        self.vy *= scale

    def _rect(self):
        """Return a pygame.Rect that bounds the ball (for collision checks)."""
        return pygame.Rect(
            int(self.x - BALL_RADIUS),
            int(self.y - BALL_RADIUS),
            BALL_RADIUS * 2,
            BALL_RADIUS * 2,
        )

    def is_below_screen(self):
        """True if the ball has fallen past the bottom (player loses a life)."""
        return self.y - BALL_RADIUS > SCREEN_HEIGHT

    def draw(self, surface):
        """Draw the ball as a filled circle."""
        pygame.draw.circle(
            surface, COLOR_BALL, (int(self.x), int(self.y)), BALL_RADIUS
        )


class Brick:
    """A single brick in the wall."""

    def __init__(self, x, y, width, height, color, row_index):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        # Bricks higher up could be worth more — uncomment the alternate
        # version below to make the top row worth the most points.
        self.points = POINTS_PER_BRICK
        # self.points = POINTS_PER_BRICK * (BRICK_ROWS - row_index)
        self.alive = True

    def draw(self, surface):
        # Fill the brick with its color, then draw a thin border around it for
        # a slightly more "polished" look. Try removing the border line for a
        # flatter, modern style.
        pygame.draw.rect(surface, self.color, self.rect, border_radius=3)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=1, border_radius=3)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_brick_wall():
    """Create and return a list of Brick objects laid out in a grid."""
    bricks = []
    for row in range(BRICK_ROWS):
        # Pick a color for this row. If there are more rows than colors in our
        # palette, we wrap around with the modulo (%) operator.
        color = BRICK_ROW_COLORS[row % len(BRICK_ROW_COLORS)]

        for col in range(BRICK_COLS):
            x = BRICK_FIELD_LEFT_MARGIN + col * (BRICK_WIDTH + BRICK_PADDING)
            y = BRICK_FIELD_TOP_MARGIN  + row * (BRICK_HEIGHT + BRICK_PADDING)
            bricks.append(Brick(x, y, BRICK_WIDTH, BRICK_HEIGHT, color, row))
    return bricks


def draw_text(surface, text, font, color, center):
    """Render `text` and blit it centered on the given (x, y) point."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=center)
    surface.blit(rendered, rect)


# =============================================================================
# MAIN GAME
# =============================================================================

def main():
    # ----- Pygame setup ------------------------------------------------------
    pygame.init()                                          # Start all pygame modules.
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()                            # Used to cap the FPS.

    # Create fonts. None as the first argument means "use the default font".
    hud_font   = pygame.font.Font(FONT_NAME, HUD_FONT_SIZE)
    big_font   = pygame.font.Font(FONT_NAME, BIG_FONT_SIZE)
    small_font = pygame.font.Font(FONT_NAME, SMALL_FONT_SIZE)

    # ----- Game state --------------------------------------------------------
    # We wrap initial setup in a small helper so "restart" can call it again.
    def new_game():
        paddle = Paddle()
        ball = Ball(paddle)
        bricks = build_brick_wall()
        return {
            "paddle": paddle,
            "ball": ball,
            "bricks": bricks,
            "score": 0,
            "lives": STARTING_LIVES,
            "game_over": False,
            "won": False,
        }

    state = new_game()

    # ----- The main game loop ------------------------------------------------
    # The loop runs once per frame. Each iteration:
    #   1) Reads input events (keyboard, window close, etc.)
    #   2) Updates the game world (move paddle, ball, check collisions)
    #   3) Draws everything to the screen
    #   4) Waits just long enough to keep us at FPS frames per second
    running = True
    while running:
        # --- 1) HANDLE EVENTS ------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User clicked the window's close button.
                running = False

            elif event.type == pygame.KEYDOWN:
                # KEYDOWN fires once per press (not continuously while held).
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Launch the ball if it's still sitting on the paddle.
                    state["ball"].launch()
                elif event.key == pygame.K_r and (state["game_over"] or state["won"]):
                    # Restart from a finished game.
                    state = new_game()

        # Continuous key state (used for paddle movement so it feels smooth).
        keys_pressed = pygame.key.get_pressed()

        # --- 2) UPDATE -------------------------------------------------------
        if not state["game_over"] and not state["won"]:
            state["paddle"].update(keys_pressed)
            scored = state["ball"].update(state["paddle"], state["bricks"])
            state["score"] += scored

            # Did we lose this ball off the bottom of the screen?
            if state["ball"].is_below_screen():
                state["lives"] -= 1
                if state["lives"] <= 0:
                    state["game_over"] = True
                else:
                    state["ball"].reset()

            # Did we clear all the bricks?
            if all(not b.alive for b in state["bricks"]):
                state["won"] = True

        # --- 3) DRAW ---------------------------------------------------------
        screen.fill(COLOR_BACKGROUND)

        # Draw bricks (only the ones that are still alive).
        for brick in state["bricks"]:
            if brick.alive:
                brick.draw(screen)

        # Draw paddle and ball.
        state["paddle"].draw(screen)
        state["ball"].draw(screen)

        # HUD (score and lives) along the top of the screen.
        score_text = f"Score: {state['score']}"
        lives_text = f"Lives: {state['lives']}"
        draw_text(screen, score_text, hud_font, COLOR_TEXT, (80, 24))
        draw_text(screen, lives_text, hud_font, COLOR_TEXT, (SCREEN_WIDTH - 80, 24))

        # "Press SPACE to launch" hint while the ball is on the paddle.
        if state["ball"].stuck_to_paddle and not state["game_over"] and not state["won"]:
            draw_text(
                screen,
                "Press SPACE to launch  |  Arrow keys to move",
                small_font,
                COLOR_TEXT_DIM,
                (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12),
            )

        # End-of-game messages.
        if state["game_over"]:
            draw_text(screen, "GAME OVER", big_font, COLOR_TEXT,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            draw_text(screen, "Press R to play again, ESC to quit",
                      small_font, COLOR_TEXT_DIM,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        elif state["won"]:
            draw_text(screen, "YOU WIN!", big_font, COLOR_TEXT,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            draw_text(screen, "Press R to play again, ESC to quit",
                      small_font, COLOR_TEXT_DIM,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))

        # Push the freshly-drawn frame to the actual window.
        pygame.display.flip()

        # --- 4) MAINTAIN FRAMERATE ------------------------------------------
        clock.tick(FPS)

    # Clean up when the loop ends.
    pygame.quit()
    sys.exit()


# This guard means "only run main() if this file was executed directly,
# not if it was imported by another script". It's a Python convention.
if __name__ == "__main__":
    main()
