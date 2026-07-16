"""
======================================================================
VERTICAL SCROLLING SHOOTER - A simple 1945/Star Force style game
======================================================================

A beginner-friendly arcade shooter written with Pygame.
You fly upward (the world scrolls down past you), shooting enemies
that fly down toward you. Avoid their bullets and don't get rammed!

CONTROLS:
    Arrow keys or WASD .... Move ship
    Space or Z ............ Shoot
    P ..................... Pause
    R ..................... Restart (after game over)
    Esc ................... Quit

REQUIREMENTS:
    Python 3.8+
    pygame   (install with: pip install pygame)

The whole game lives in this single file and uses NO external
images, sounds, or fonts. Everything visual is drawn with Pygame's
basic shape primitives so you can read and tweak it easily.
"""

import math
import random
import sys

import pygame


# =====================================================================
# CONFIGURATION CONSTANTS
# =====================================================================
# Tweak any of these to change how the game looks and feels.
# They are grouped by topic so you can find what you want quickly.
# ---------------------------------------------------------------------

# --- Window / display -------------------------------------------------
SCREEN_WIDTH = 480           # Window width in pixels.  Try 360 for a
                             # narrower "arcade cabinet" feel, or 600+ for
                             # more room to dodge.
SCREEN_HEIGHT = 720           # Window height in pixels.  Vertical shooters
                              # traditionally use a tall (portrait) screen.
FPS = 60                      # Frames per second.  Higher = smoother, but
                              # more CPU.  All movement values below are
                              # tuned for 60 FPS.
WINDOW_TITLE = "Sky Striker"  # Text in the window's title bar.

# --- Colors (RGB tuples, 0..255) -------------------------------------
# Change these to recolor the entire game.
COLOR_BG_TOP    = (5, 5, 30)       # Sky color at the top of the screen.
COLOR_BG_BOTTOM = (20, 0, 50)      # Sky color at the bottom (gradient).
COLOR_STAR      = (255, 255, 255)  # Color of the scrolling star field.
COLOR_PLAYER    = (90, 200, 255)   # Player ship body.
COLOR_PLAYER_HI = (220, 240, 255)  # Player ship cockpit highlight.
COLOR_PLAYER_THRUST = (255, 180, 60)  # Engine flame.
COLOR_PLAYER_BULLET = (255, 240, 120)  # Your bullets.
COLOR_ENEMY     = (255, 80, 80)    # Standard enemy color.
COLOR_ENEMY_FAST = (255, 160, 60)  # Fast (smaller) enemy color.
COLOR_ENEMY_TANK = (160, 80, 200)  # Tough (larger) enemy color.
COLOR_ENEMY_BULLET = (255, 120, 200)  # Enemy bullets.
COLOR_EXPLOSION = (255, 200, 80)   # Explosion particles.
COLOR_HUD_TEXT  = (230, 230, 230)  # Score / lives text.
COLOR_HUD_DIM   = (140, 140, 160)  # Less important HUD text.

# --- Star field (background) -----------------------------------------
NUM_STARS = 80                # How many stars are visible at once.
                              # Lower this on slow machines.
STAR_SPEED_MIN = 1.0          # Slowest star speed (pixels/frame).
STAR_SPEED_MAX = 4.0          # Fastest star speed.  The variation is
                              # what creates the parallax depth effect.

# --- Player ship ------------------------------------------------------
PLAYER_WIDTH = 36             # Ship hitbox/visual width.
PLAYER_HEIGHT = 36            # Ship hitbox/visual height.
PLAYER_SPEED = 5.5            # Movement speed in pixels/frame.  Higher
                              # = twitchier; lower = more deliberate.
PLAYER_FIRE_COOLDOWN_MS = 180 # Milliseconds between shots.  Lower this
                              # for a rapid-fire feel.
PLAYER_START_LIVES = 3        # Extra lives on a fresh game.
PLAYER_INVULN_MS = 1500       # How long the player flashes and is
                              # immune after losing a life.

# --- Bullets ----------------------------------------------------------
PLAYER_BULLET_SPEED = 10.0    # How fast your shots travel upward.
PLAYER_BULLET_WIDTH = 4
PLAYER_BULLET_HEIGHT = 14

ENEMY_BULLET_SPEED = 4.5      # How fast enemy shots travel downward.
                              # Keep this well below player bullet speed
                              # so the player can outrun their own shots.
ENEMY_BULLET_RADIUS = 5

# --- Enemies ----------------------------------------------------------
# We have three "kinds" of enemies. Each kind has its own stats below.
# A new enemy spawns roughly every ENEMY_SPAWN_INTERVAL_MS milliseconds.
ENEMY_SPAWN_INTERVAL_MS = 800   # Lower = more enemies = harder.
ENEMY_SPAWN_JITTER_MS = 400     # Random extra time added to each spawn,
                                # so the rhythm doesn't feel mechanical.

# Probability weights for each enemy type. They don't need to sum to 1.0;
# they're relative to each other.
ENEMY_WEIGHT_BASIC = 6.0
ENEMY_WEIGHT_FAST  = 3.0
ENEMY_WEIGHT_TANK  = 1.0

# Basic enemy: average size, average speed, 1 HP.
ENEMY_BASIC_SIZE = 32
ENEMY_BASIC_SPEED = 2.2
ENEMY_BASIC_HP = 1
ENEMY_BASIC_SCORE = 100
ENEMY_BASIC_FIRE_CHANCE = 0.004  # Per-frame chance to shoot.  At 60 FPS,
                                 # 0.004 ≈ once every ~4 seconds per enemy.

# Fast enemy: small, quick, can't take a punch but rarely shoots.
ENEMY_FAST_SIZE = 24
ENEMY_FAST_SPEED = 4.0
ENEMY_FAST_HP = 1
ENEMY_FAST_SCORE = 200
ENEMY_FAST_FIRE_CHANCE = 0.002

# Tank enemy: big, slow, takes several hits, fires more often.
ENEMY_TANK_SIZE = 48
ENEMY_TANK_SPEED = 1.4
ENEMY_TANK_HP = 4
ENEMY_TANK_SCORE = 400
ENEMY_TANK_FIRE_CHANCE = 0.008

# Difficulty ramp: every DIFFICULTY_RAMP_SECONDS, spawn interval shrinks
# by DIFFICULTY_RAMP_FACTOR (multiplicative). Set RAMP_FACTOR to 1.0 to
# disable the ramp entirely.
DIFFICULTY_RAMP_SECONDS = 20
DIFFICULTY_RAMP_FACTOR = 0.92
ENEMY_SPAWN_INTERVAL_MIN_MS = 250  # Floor — never spawn faster than this.

# --- Explosions / particles ------------------------------------------
EXPLOSION_PARTICLES = 14      # Particles per explosion.  Bigger numbers
                              # look juicier but cost more performance.
EXPLOSION_SPEED_MIN = 1.0
EXPLOSION_SPEED_MAX = 4.0
EXPLOSION_LIFE_FRAMES = 30    # How many frames each particle lives.

# --- HUD --------------------------------------------------------------
HUD_FONT_SIZE = 22
HUD_MARGIN = 10               # Distance from screen edges, in pixels.

# =====================================================================
# END OF CONFIGURATION
# =====================================================================


# ---------------------------------------------------------------------
# Helper: pick a weighted random choice.
# ---------------------------------------------------------------------
# random.choices does this for us, but a tiny wrapper makes the calling
# code easier to read.
def weighted_choice(options_with_weights):
    """Return one option chosen by weight.

    `options_with_weights` is a list of (option, weight) tuples.
    """
    options = [pair[0] for pair in options_with_weights]
    weights = [pair[1] for pair in options_with_weights]
    return random.choices(options, weights=weights, k=1)[0]


# ---------------------------------------------------------------------
# Star: a single twinkling dot in the parallax background.
# ---------------------------------------------------------------------
class Star:
    """One pixel of the scrolling star field.

    Stars at different speeds create a sense of depth (parallax):
    fast stars feel close, slow stars feel far away.
    """
    def __init__(self):
        # Pick a random position and a random speed.
        # We re-randomize on respawn (when the star scrolls off the bottom).
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(0, SCREEN_HEIGHT)
        self.speed = random.uniform(STAR_SPEED_MIN, STAR_SPEED_MAX)
        # Faster stars are drawn brighter to enhance the depth illusion.
        brightness_ratio = (self.speed - STAR_SPEED_MIN) / max(
            0.0001, (STAR_SPEED_MAX - STAR_SPEED_MIN)
        )
        gray = int(120 + 135 * brightness_ratio)  # 120..255
        self.color = (gray, gray, gray)

    def update(self):
        # Move down by the star's speed each frame.
        self.y += self.speed
        # Wrap to the top once we leave the screen.
        if self.y > SCREEN_HEIGHT:
            self.y = 0.0
            self.x = random.uniform(0, SCREEN_WIDTH)
            # Re-pick speed/brightness for variety.
            self.speed = random.uniform(STAR_SPEED_MIN, STAR_SPEED_MAX)

    def draw(self, surface):
        # A 1- or 2-pixel rectangle is cheaper than a circle and looks fine.
        size = 1 if self.speed < (STAR_SPEED_MIN + STAR_SPEED_MAX) / 2 else 2
        surface.fill(self.color, (int(self.x), int(self.y), size, size))


# ---------------------------------------------------------------------
# Bullet: used for both the player's shots and enemy shots.
# ---------------------------------------------------------------------
class Bullet:
    """A simple projectile that moves in a straight line.

    `vy` (vertical velocity) is negative for upward (player) shots
    and positive for downward (enemy) shots. The same class handles both.
    """
    def __init__(self, x, y, vy, color, is_player_bullet):
        self.x = x
        self.y = y
        self.vy = vy
        self.color = color
        self.is_player_bullet = is_player_bullet
        self.alive = True
        # Player bullets are little rectangles; enemy bullets are circles.
        # That makes it easier for the player to distinguish friend from foe
        # at a glance — a small but important readability trick.
        if is_player_bullet:
            self.rect = pygame.Rect(
                int(x - PLAYER_BULLET_WIDTH / 2),
                int(y - PLAYER_BULLET_HEIGHT / 2),
                PLAYER_BULLET_WIDTH,
                PLAYER_BULLET_HEIGHT,
            )
        else:
            r = ENEMY_BULLET_RADIUS
            self.rect = pygame.Rect(int(x - r), int(y - r), r * 2, r * 2)

    def update(self):
        self.y += self.vy
        # Sync the collision rectangle to the new position.
        self.rect.centery = int(self.y)
        self.rect.centerx = int(self.x)
        # Mark dead once off-screen (top or bottom).
        if self.y < -20 or self.y > SCREEN_HEIGHT + 20:
            self.alive = False

    def draw(self, surface):
        if self.is_player_bullet:
            # A bright rectangle with a slightly lighter center for "pew" feel.
            pygame.draw.rect(surface, self.color, self.rect, border_radius=2)
        else:
            pygame.draw.circle(
                surface, self.color, (int(self.x), int(self.y)),
                ENEMY_BULLET_RADIUS,
            )
            # Inner highlight makes enemy bullets pop against dark sky.
            pygame.draw.circle(
                surface, (255, 230, 240),
                (int(self.x), int(self.y)),
                max(1, ENEMY_BULLET_RADIUS - 2),
            )


# ---------------------------------------------------------------------
# Player: the ship you control.
# ---------------------------------------------------------------------
class Player:
    """The player's ship.

    Holds position, lives, and shooting cooldown. Also handles brief
    invulnerability after being hit, so the player isn't instantly killed
    again after respawning at the center.
    """
    def __init__(self):
        # Start near the bottom-center.
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT * 1.5
        self.lives = PLAYER_START_LIVES
        self.last_shot_time_ms = 0
        # When pygame.time.get_ticks() < invuln_until_ms, we ignore hits
        # and flicker the sprite to signal "just respawned".
        self.invuln_until_ms = pygame.time.get_ticks() + PLAYER_INVULN_MS

        # The collision rectangle. We center it on (x, y) and update each
        # frame inside `update`.
        self.rect = pygame.Rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.rect.center = (int(self.x), int(self.y))

    def is_invulnerable(self, now_ms):
        return now_ms < self.invuln_until_ms

    def update(self, keys, now_ms):
        # --- Movement --------------------------------------------------
        # Read both arrow keys and WASD so users can pick.
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP]    or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]:
            dy += 1.0

        # Diagonal movement should not be faster than straight movement.
        # We normalize the (dx, dy) vector so its length is 1, then scale
        # by PLAYER_SPEED. This is a classic 2D-game gotcha worth knowing!
        if dx != 0.0 or dy != 0.0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        self.x += dx * PLAYER_SPEED
        self.y += dy * PLAYER_SPEED

        # Keep the ship inside the play area.
        half_w = PLAYER_WIDTH / 2
        half_h = PLAYER_HEIGHT / 2
        if self.x < half_w:
            self.x = half_w
        if self.x > SCREEN_WIDTH - half_w:
            self.x = SCREEN_WIDTH - half_w
        if self.y < half_h:
            self.y = half_h
        if self.y > SCREEN_HEIGHT - half_h:
            self.y = SCREEN_HEIGHT - half_h

        self.rect.center = (int(self.x), int(self.y))

    def can_shoot(self, now_ms):
        return (now_ms - self.last_shot_time_ms) >= PLAYER_FIRE_COOLDOWN_MS

    def shoot(self, bullets, now_ms):
        """Spawn a bullet just above the ship's nose."""
        if not self.can_shoot(now_ms):
            return
        self.last_shot_time_ms = now_ms
        bullets.append(Bullet(
            x=self.x,
            y=self.y - PLAYER_HEIGHT / 2,
            vy=-PLAYER_BULLET_SPEED,    # Negative = moving UP the screen.
            color=COLOR_PLAYER_BULLET,
            is_player_bullet=True,
        ))

    def hit(self, now_ms):
        """Called when an enemy or enemy bullet touches the ship.

        Returns True if the hit actually counted (i.e., not invulnerable).
        """
        if self.is_invulnerable(now_ms):
            return False
        self.lives -= 1
        # Re-grant invulnerability so the next frame doesn't kill us again.
        self.invuln_until_ms = now_ms + PLAYER_INVULN_MS
        # Recenter the ship so the player has a moment to reorient.
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT * 1.5
        self.rect.center = (int(self.x), int(self.y))
        return True

    def draw(self, surface, now_ms):
        # Flicker while invulnerable: skip drawing every other ~80 ms.
        if self.is_invulnerable(now_ms):
            # Integer-divide the time to get a slow on/off cycle.
            if (now_ms // 80) % 2 == 0:
                return  # Skip this frame's draw; ship "blinks".

        cx, cy = int(self.x), int(self.y)
        hw = PLAYER_WIDTH // 2
        hh = PLAYER_HEIGHT // 2

        # Engine flame behind the ship — drawn first so it sits *under* the body.
        # The flame jitters a few pixels each frame for an animated feel.
        flame_jitter = random.randint(-2, 2)
        flame_points = [
            (cx - 6, cy + hh - 2),
            (cx + 6, cy + hh - 2),
            (cx,     cy + hh + 10 + flame_jitter),
        ]
        pygame.draw.polygon(surface, COLOR_PLAYER_THRUST, flame_points)

        # The hull: a triangle pointing UP (since we shoot upward).
        hull_points = [
            (cx,         cy - hh),       # Nose
            (cx - hw,    cy + hh - 4),   # Bottom-left
            (cx + hw,    cy + hh - 4),   # Bottom-right
        ]
        pygame.draw.polygon(surface, COLOR_PLAYER, hull_points)

        # Wings: two small rectangles sticking out the sides.
        pygame.draw.rect(surface, COLOR_PLAYER,
                         (cx - hw - 4, cy + 2, 6, 10))
        pygame.draw.rect(surface, COLOR_PLAYER,
                         (cx + hw - 2, cy + 2, 6, 10))

        # Cockpit highlight: a small circle near the nose.
        pygame.draw.circle(surface, COLOR_PLAYER_HI, (cx, cy - 2), 4)


# ---------------------------------------------------------------------
# Enemy: comes in three flavors driven by `kind`.
# ---------------------------------------------------------------------
class Enemy:
    """An enemy ship that flies down and occasionally shoots.

    `kind` is one of "basic", "fast", "tank". Each kind reads its own
    constants from the configuration block above. Centralizing them
    there means you can rebalance the game without touching this code.
    """
    def __init__(self, kind):
        self.kind = kind
        if kind == "fast":
            self.size = ENEMY_FAST_SIZE
            self.speed = ENEMY_FAST_SPEED
            self.hp = ENEMY_FAST_HP
            self.score = ENEMY_FAST_SCORE
            self.fire_chance = ENEMY_FAST_FIRE_CHANCE
            self.color = COLOR_ENEMY_FAST
        elif kind == "tank":
            self.size = ENEMY_TANK_SIZE
            self.speed = ENEMY_TANK_SPEED
            self.hp = ENEMY_TANK_HP
            self.score = ENEMY_TANK_SCORE
            self.fire_chance = ENEMY_TANK_FIRE_CHANCE
            self.color = COLOR_ENEMY_TANK
        else:  # "basic"
            self.size = ENEMY_BASIC_SIZE
            self.speed = ENEMY_BASIC_SPEED
            self.hp = ENEMY_BASIC_HP
            self.score = ENEMY_BASIC_SCORE
            self.fire_chance = ENEMY_BASIC_FIRE_CHANCE
            self.color = COLOR_ENEMY

        # Spawn at a random horizontal position, just above the screen.
        half = self.size / 2
        self.x = random.uniform(half, SCREEN_WIDTH - half)
        self.y = -half

        # Light side-to-side wobble so enemies don't fly in straight lines.
        # `wobble_phase` is just the starting angle of the sine wave.
        self.wobble_phase = random.uniform(0, math.tau)
        self.wobble_amount = random.uniform(0.5, 1.5)
        # `age_frames` drives the wobble over time.
        self.age_frames = 0

        self.alive = True
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (int(self.x), int(self.y))

    def update(self, bullets):
        # Move straight down + a little sideways sine-wave wobble.
        self.age_frames += 1
        self.y += self.speed
        wobble_dx = math.sin(self.age_frames * 0.05 + self.wobble_phase)
        self.x += wobble_dx * self.wobble_amount

        # Stay on-screen horizontally (for tanks especially, the sprite is wide).
        half = self.size / 2
        if self.x < half:
            self.x = half
        if self.x > SCREEN_WIDTH - half:
            self.x = SCREEN_WIDTH - half

        self.rect.center = (int(self.x), int(self.y))

        # If we've left the bottom, mark dead so the game removes us.
        if self.y - half > SCREEN_HEIGHT:
            self.alive = False
            return

        # Random chance to shoot. Only shoot once we're actually on-screen,
        # so the player isn't surprised by bullets from invisible enemies.
        if self.y > 0 and random.random() < self.fire_chance:
            bullets.append(Bullet(
                x=self.x,
                y=self.y + half,
                vy=ENEMY_BULLET_SPEED,   # Positive = moving DOWN.
                color=COLOR_ENEMY_BULLET,
                is_player_bullet=False,
            ))

    def take_damage(self, amount=1):
        """Subtract HP and return True if the enemy just died."""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        half = self.size // 2

        # Body: a triangle pointing DOWN (toward the player).
        body = [
            (cx,         cy + half),       # Bottom point
            (cx - half,  cy - half + 4),   # Top-left
            (cx + half,  cy - half + 4),   # Top-right
        ]
        pygame.draw.polygon(surface, self.color, body)

        # Tank enemies get an extra "armor band" rectangle for visual weight.
        if self.kind == "tank":
            pygame.draw.rect(
                surface, (40, 20, 60),
                (cx - half + 4, cy - 4, self.size - 8, 8),
            )

        # A small dark "cockpit" circle near the top.
        pygame.draw.circle(surface, (30, 0, 30), (cx, cy - half + 8), 4)


# ---------------------------------------------------------------------
# Particle: a single dot in an explosion.
# ---------------------------------------------------------------------
class Particle:
    """One spark of an explosion.

    Particles are intentionally simple — just position, velocity, and a
    countdown timer. When the timer hits zero, they're removed.
    """
    def __init__(self, x, y):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(EXPLOSION_SPEED_MIN, EXPLOSION_SPEED_MAX)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = EXPLOSION_LIFE_FRAMES
        # A tiny size variation makes the explosion look less uniform.
        self.size = random.randint(2, 4)
        # Slight color variation per particle.
        r = min(255, COLOR_EXPLOSION[0] + random.randint(-20, 20))
        g = min(255, COLOR_EXPLOSION[1] + random.randint(-30, 30))
        b = min(255, COLOR_EXPLOSION[2] + random.randint(-20, 20))
        self.color = (max(0, r), max(0, g), max(0, b))

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # A bit of "drag" so particles slow to a halt instead of flying off.
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surface):
        # Particles fade out by shrinking near end-of-life.
        # (We could also fade alpha, but that's slower and not needed here.)
        s = self.size if self.life > 8 else max(1, self.size - 1)
        surface.fill(self.color, (int(self.x), int(self.y), s, s))


# ---------------------------------------------------------------------
# Game: the top-level state machine.
# ---------------------------------------------------------------------
class Game:
    """Owns every entity and the main loop's per-frame logic.

    Putting the loop body in methods keeps `main()` short and makes it
    easy for a beginner to find a specific feature (e.g. "where do
    collisions happen?" -> `_handle_collisions`).
    """
    # State constants — using plain strings keeps them readable when printed.
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_GAME_OVER = "game_over"

    def __init__(self, screen, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small
        self.reset()

    def reset(self):
        """Start (or restart) a fresh game."""
        self.state = Game.STATE_PLAYING
        self.score = 0

        self.player = Player()
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = []

        self.stars = [Star() for _ in range(NUM_STARS)]

        # Spawn timing:
        now_ms = pygame.time.get_ticks()
        self.next_enemy_spawn_ms = now_ms + ENEMY_SPAWN_INTERVAL_MS
        self.current_spawn_interval_ms = ENEMY_SPAWN_INTERVAL_MS
        self.last_difficulty_ramp_ms = now_ms
        self.start_ms = now_ms

    # -----------------------------------------------------------------
    # Spawning
    # -----------------------------------------------------------------
    def _maybe_spawn_enemy(self, now_ms):
        if now_ms < self.next_enemy_spawn_ms:
            return
        kind = weighted_choice([
            ("basic", ENEMY_WEIGHT_BASIC),
            ("fast",  ENEMY_WEIGHT_FAST),
            ("tank",  ENEMY_WEIGHT_TANK),
        ])
        self.enemies.append(Enemy(kind))
        # Schedule the next spawn with a little randomness.
        jitter = random.randint(-ENEMY_SPAWN_JITTER_MS, ENEMY_SPAWN_JITTER_MS)
        self.next_enemy_spawn_ms = (
            now_ms + max(50, self.current_spawn_interval_ms + jitter)
        )

    def _maybe_ramp_difficulty(self, now_ms):
        # Every DIFFICULTY_RAMP_SECONDS, shrink the spawn interval.
        if now_ms - self.last_difficulty_ramp_ms < DIFFICULTY_RAMP_SECONDS * 1000:
            return
        self.last_difficulty_ramp_ms = now_ms
        new_interval = self.current_spawn_interval_ms * DIFFICULTY_RAMP_FACTOR
        self.current_spawn_interval_ms = max(
            ENEMY_SPAWN_INTERVAL_MIN_MS, new_interval
        )

    def _spawn_explosion(self, x, y):
        for _ in range(EXPLOSION_PARTICLES):
            self.particles.append(Particle(x, y))

    # -----------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Pause toggling
            if event.key == pygame.K_p and self.state == Game.STATE_PLAYING:
                self.state = Game.STATE_PAUSED
            elif event.key == pygame.K_p and self.state == Game.STATE_PAUSED:
                self.state = Game.STATE_PLAYING
            # Restart after game over
            elif event.key == pygame.K_r and self.state == Game.STATE_GAME_OVER:
                self.reset()

    def _handle_continuous_input(self, now_ms):
        keys = pygame.key.get_pressed()
        self.player.update(keys, now_ms)
        # Holding Space or Z = continuous fire (rate-limited by cooldown).
        if keys[pygame.K_SPACE] or keys[pygame.K_z]:
            self.player.shoot(self.player_bullets, now_ms)

    # -----------------------------------------------------------------
    # Per-frame update
    # -----------------------------------------------------------------
    def update(self):
        if self.state != Game.STATE_PLAYING:
            return  # Pause and game-over freeze the world.

        now_ms = pygame.time.get_ticks()

        # 1) Background
        for star in self.stars:
            star.update()

        # 2) Input + player movement / shooting
        self._handle_continuous_input(now_ms)

        # 3) Bullets
        for b in self.player_bullets:
            b.update()
        for b in self.enemy_bullets:
            b.update()

        # 4) Enemies
        self._maybe_ramp_difficulty(now_ms)
        self._maybe_spawn_enemy(now_ms)
        for e in self.enemies:
            e.update(self.enemy_bullets)

        # 5) Particles
        for p in self.particles:
            p.update()

        # 6) Collisions
        self._handle_collisions(now_ms)

        # 7) Cull dead objects.
        # Doing this *after* collision keeps the per-frame logic tidy:
        # collisions just flip `alive` flags or call hit/take_damage.
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets  = [b for b in self.enemy_bullets  if b.alive]
        self.enemies        = [e for e in self.enemies        if e.alive]
        self.particles      = [p for p in self.particles      if p.alive]

        # 8) Game over check
        if self.player.lives <= 0:
            self.state = Game.STATE_GAME_OVER

    def _handle_collisions(self, now_ms):
        # --- Player bullets vs enemies --------------------------------
        # rect-vs-rect collision is plenty for an arcade shooter; no need
        # for pixel-perfect masks.
        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if bullet.rect.colliderect(enemy.rect):
                    bullet.alive = False
                    died = enemy.take_damage(1)
                    if died:
                        self.score += enemy.score
                        self._spawn_explosion(enemy.x, enemy.y)
                    break  # One bullet, one hit.

        # --- Enemy bullets vs player ----------------------------------
        for bullet in self.enemy_bullets:
            if not bullet.alive:
                continue
            if bullet.rect.colliderect(self.player.rect):
                bullet.alive = False
                if self.player.hit(now_ms):
                    self._spawn_explosion(self.player.x, self.player.y)

        # --- Enemies vs player (ramming) ------------------------------
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.rect.colliderect(self.player.rect):
                if self.player.hit(now_ms):
                    self._spawn_explosion(self.player.x, self.player.y)
                # Ramming kills the enemy too — feels fair and clears the screen.
                enemy.alive = False
                self.score += enemy.score // 2
                self._spawn_explosion(enemy.x, enemy.y)

    # -----------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------
    def draw(self):
        self._draw_background()

        for star in self.stars:
            star.draw(self.screen)

        for e in self.enemies:
            e.draw(self.screen)

        for b in self.player_bullets:
            b.draw(self.screen)
        for b in self.enemy_bullets:
            b.draw(self.screen)

        # Player on top of bullets so it's never hidden by its own shots.
        now_ms = pygame.time.get_ticks()
        self.player.draw(self.screen, now_ms)

        for p in self.particles:
            p.draw(self.screen)

        self._draw_hud()

        # Overlay messages
        if self.state == Game.STATE_PAUSED:
            self._draw_center_message("PAUSED", "Press P to resume")
        elif self.state == Game.STATE_GAME_OVER:
            self._draw_center_message(
                "GAME OVER",
                f"Final score: {self.score}    Press R to restart",
            )

    def _draw_background(self):
        # A very simple top-to-bottom gradient using horizontal lines.
        # For a flat color, replace this whole method with screen.fill(...).
        for y in range(SCREEN_HEIGHT):
            t = y / max(1, SCREEN_HEIGHT - 1)  # 0.0 .. 1.0
            r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * t)
            g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * t)
            b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_hud(self):
        # Score (top-left)
        score_surf = self.font_small.render(
            f"SCORE  {self.score:07d}", True, COLOR_HUD_TEXT
        )
        self.screen.blit(score_surf, (HUD_MARGIN, HUD_MARGIN))

        # Lives (top-right) — one tiny ship icon per life.
        lives_label = self.font_small.render("LIVES", True, COLOR_HUD_DIM)
        self.screen.blit(
            lives_label,
            (SCREEN_WIDTH - HUD_MARGIN - lives_label.get_width() - 8 - 18 * self.player.lives,
             HUD_MARGIN),
        )
        for i in range(self.player.lives):
            icon_x = SCREEN_WIDTH - HUD_MARGIN - (i + 1) * 18
            icon_y = HUD_MARGIN + 4
            # Mini triangle in the player's color.
            points = [
                (icon_x + 7,  icon_y),
                (icon_x,      icon_y + 14),
                (icon_x + 14, icon_y + 14),
            ]
            pygame.draw.polygon(self.screen, COLOR_PLAYER, points)

        # Hint line (bottom-left) — only while playing, fades after a bit.
        elapsed_ms = pygame.time.get_ticks() - self.start_ms
        if self.state == Game.STATE_PLAYING and elapsed_ms < 4000:
            hint = self.font_small.render(
                "Move: arrows/WASD   Shoot: Space/Z   Pause: P",
                True, COLOR_HUD_DIM,
            )
            self.screen.blit(
                hint,
                (HUD_MARGIN, SCREEN_HEIGHT - HUD_MARGIN - hint.get_height()),
            )

    def _draw_center_message(self, big_text, small_text):
        # Translucent dark veil makes overlay text readable.
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))  # The 4th value is alpha (0..255).
        self.screen.blit(veil, (0, 0))

        big_surf = self.font_big.render(big_text, True, COLOR_HUD_TEXT)
        small_surf = self.font_small.render(small_text, True, COLOR_HUD_TEXT)

        self.screen.blit(
            big_surf,
            (SCREEN_WIDTH // 2 - big_surf.get_width() // 2,
             SCREEN_HEIGHT // 2 - big_surf.get_height()),
        )
        self.screen.blit(
            small_surf,
            (SCREEN_WIDTH // 2 - small_surf.get_width() // 2,
             SCREEN_HEIGHT // 2 + 8),
        )


# ---------------------------------------------------------------------
# main(): set up Pygame, then run the loop until the user quits.
# ---------------------------------------------------------------------
def main():
    # pygame.init initializes ALL pygame submodules (display, font, ...).
    # If you're worried about startup time, you can init them individually.
    pygame.init()

    # Create the window. The flags argument (3rd positional) can include
    # pygame.RESIZABLE or pygame.FULLSCREEN if you want to experiment.
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # The Clock keeps the frame rate steady. tick(FPS) sleeps just long
    # enough to hold the game at FPS frames per second.
    clock = pygame.time.Clock()

    # We use the default system font (None) so we don't need a .ttf file.
    # Try changing the family name to e.g. "consolas" or "couriernew" for
    # a different look — pygame will fall back to a default if not found.
    font_small = pygame.font.SysFont(None, HUD_FONT_SIZE)
    font_big   = pygame.font.SysFont(None, HUD_FONT_SIZE * 3, bold=True)

    game = Game(screen, font_big, font_small)

    # The main loop. This pattern — events, update, draw, flip — is the
    # backbone of essentially every Pygame game.
    running = True
    while running:
        # 1) Process discrete events (key presses, window close, ...).
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                game.handle_event(event)

        # 2) Update the game state.
        game.update()

        # 3) Draw the new frame.
        game.draw()

        # 4) Show what we drew.
        pygame.display.flip()

        # 5) Wait so we hit (at most) FPS frames per second.
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


# Standard "only run when executed directly, not when imported" idiom.
if __name__ == "__main__":
    main()
