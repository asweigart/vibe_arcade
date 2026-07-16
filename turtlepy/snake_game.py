"""
Snake Game - Built with Python's turtle module
================================================
A classic snake game where you guide a green snake around the board,
eating red apples to grow longer. Avoid walls and your own tail!

Controls:
  Arrow keys or WASD to move
  Space to start / restart
  Click the window to start on the title screen

How to read this code:
  1. Constants at the top control the game's look and feel.
  2. The game board is a grid of squares. Each square has a column (x) and row (y).
  3. The snake is a list of (column, row) positions. The first item is the head.
  4. Every "tick" the snake moves one square in its current direction.
  5. Wall layouts are defined as multi-line strings using '#' for wall blocks.
"""

import turtle
import random

# =============================================================================
# CONSTANTS - Change these to customize the game!
# =============================================================================

# --- Grid and Window ---
GRID_SIZE = 20          # Number of squares across and down (try 15 for small, 25 for large)
SQUARE_SIZE = 30        # Pixel size of each grid square (smaller = smaller window)
WINDOW_TITLE = "Snake Game"

# --- Colors ---
BACKGROUND_COLOR = "black"
SNAKE_COLOR = "green"
SNAKE_HEAD_COLOR = "#00CC00"   # A slightly brighter green for the head
APPLE_COLOR = "red"
WALL_COLOR = "gray"
BORDER_COLOR = "white"         # Color of the border around the play area
GRID_LINE_COLOR = "#1a1a1a"    # Faint grid lines (set to BACKGROUND_COLOR to hide)
TEXT_COLOR = "white"
SCORE_COLOR = "white"

# --- Gameplay ---
STARTING_LENGTH = 3           # How many squares long the snake starts (minimum 1)
STARTING_SPEED = 8            # Moves per second at the start (higher = faster)
MAX_SPEED = 20                # The fastest the game will ever go
SPEED_INCREASE = 0.3          # How much faster (moves/sec) per apple eaten (try 0.5 for harder)

# --- Starting position and direction ---
# The snake starts near the center of the grid, moving to the right.
START_COLUMN = GRID_SIZE // 4
START_ROW = GRID_SIZE // 2
START_DIRECTION = "right"

# --- Score display ---
SCORE_FONT = ("Arial", 16, "bold")
TITLE_FONT = ("Arial", 28, "bold")
SUBTITLE_FONT = ("Arial", 16, "normal")
GAME_OVER_FONT = ("Arial", 24, "bold")

# =============================================================================
# WALL LAYOUTS
# =============================================================================
# Each layout is a multi-line string. '#' marks a wall block, and any other
# character (like a space or dot) is open floor. The layout is drawn starting
# from the top-left corner of the grid. If a layout is bigger than the grid,
# the extra parts are simply ignored (truncated).
#
# The first game is always BLANK (no walls). After that, a random layout
# is chosen from this list each time you restart.
#
# Feel free to add your own layouts! Just add another string to this list.
# =============================================================================

WALL_LAYOUTS = [
    # --- Layout 1: Cross in the center ---
    """\
..........#.........
..........#.........
..........#.........
..........#.........
....................
....................
....................
....................
....................
####..........####..
....................
....................
....................
....................
....................
....................
..........#.........
..........#.........
..........#.........
..........#.........
""",

    # --- Layout 2: Four pillars ---
    """\
....................
....................
....................
....................
.....#........#.....
.....#........#.....
.....#........#.....
....................
....................
....................
....................
....................
....................
.....#........#.....
.....#........#.....
.....#........#.....
....................
....................
....................
....................
""",

    # --- Layout 3: Spiral-ish path ---
    """\
....................
.################...
....................
...################.
....................
.################...
....................
...################.
....................
....................
....................
....................
.################...
....................
...################.
....................
.################...
....................
...################.
....................
""",

    # --- Layout 4: Scattered blocks ---
    """\
....................
....................
...##.........##....
...##.........##....
....................
....................
.........##.........
.........##.........
....................
....................
....................
....................
.........##.........
.........##.........
....................
....................
...##.........##....
...##.........##....
....................
....................
""",

    # --- Layout 5: Border gap maze ---
    """\
....................
.##################.
.#................#.
.#................#.
.#................#.
.#....          .#.
.#................#.
.......      .......
....................
....................
....................
....................
.......      .......
.#................#.
.#................#.
.#................#.
.#................#.
.#................#.
.##################.
....................
""",

    # --- Layout 6: Diamond ---
    """\
..........#.........
.........#.#........
........#...#.......
.......#.....#......
......#.......#.....
.....#.........#....
......#.......#.....
.......#.....#......
........#...#.......
.........#.#........
..........#.........
....................
....................
....................
....................
....................
....................
....................
....................
....................
""",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def grid_to_pixel(column, row):
    """
    Convert a grid position (column, row) to pixel coordinates on screen.

    The grid's top-left corner is at column=0, row=0.
    Pixel (0, 0) is at the center of the screen in turtle graphics,
    so we need to offset everything so the grid is centered.
    """
    # Calculate the total pixel size of the grid
    total_size = GRID_SIZE * SQUARE_SIZE

    # Find where the top-left corner of the grid should be in pixels
    grid_left = -total_size // 2
    grid_top = total_size // 2

    # Calculate the pixel position for this grid square
    pixel_x = grid_left + (column * SQUARE_SIZE) + (SQUARE_SIZE // 2)
    pixel_y = grid_top - (row * SQUARE_SIZE) - (SQUARE_SIZE // 2)

    return pixel_x, pixel_y


def parse_wall_layout(layout_string):
    """
    Turn a wall layout string into a list of (column, row) positions.

    Each '#' character in the string becomes a wall block on the grid.
    If the layout is bigger than the grid, extra parts are ignored.
    """
    wall_positions = []

    # Split the string into lines (rows of the grid)
    lines = layout_string.strip().split("\n")

    for row_index, line in enumerate(lines):
        # Stop if we've gone past the bottom of the grid
        if row_index >= GRID_SIZE:
            break

        for col_index, character in enumerate(line):
            # Stop if we've gone past the right edge of the grid
            if col_index >= GRID_SIZE:
                break

            # A '#' means this square is a wall
            if character == "#":
                wall_positions.append((col_index, row_index))

    return wall_positions


# =============================================================================
# DRAWING FUNCTIONS
# =============================================================================

def draw_square(drawer, column, row, color):
    """
    Draw a single filled square on the grid at the given column and row.

    'drawer' is a turtle object used for stamping or drawing.
    """
    pixel_x, pixel_y = grid_to_pixel(column, row)
    drawer.goto(pixel_x, pixel_y)
    drawer.color(color)
    drawer.stamp()


def draw_border(drawer):
    """
    Draw a white border around the entire play area.
    """
    total_size = GRID_SIZE * SQUARE_SIZE
    half = total_size // 2

    drawer.penup()
    drawer.color(BORDER_COLOR)
    drawer.pensize(2)

    # Move to the top-left corner
    drawer.goto(-half, half)
    drawer.pendown()

    # Draw all four sides of the rectangle
    drawer.goto(half, half)     # top-right
    drawer.goto(half, -half)    # bottom-right
    drawer.goto(-half, -half)   # bottom-left
    drawer.goto(-half, half)    # back to top-left

    drawer.penup()


def draw_grid_lines(drawer):
    """
    Draw faint grid lines so players can see the squares.
    """
    total_size = GRID_SIZE * SQUARE_SIZE
    half = total_size // 2

    drawer.penup()
    drawer.color(GRID_LINE_COLOR)
    drawer.pensize(1)

    # Draw vertical lines
    for col in range(1, GRID_SIZE):
        x = -half + (col * SQUARE_SIZE)
        drawer.goto(x, half)
        drawer.pendown()
        drawer.goto(x, -half)
        drawer.penup()

    # Draw horizontal lines
    for row in range(1, GRID_SIZE):
        y = half - (row * SQUARE_SIZE)
        drawer.goto(-half, y)
        drawer.pendown()
        drawer.goto(half, y)
        drawer.penup()


# =============================================================================
# GAME CLASS
# =============================================================================

class SnakeGame:
    """
    The main game class. It holds all the game state and handles
    input, drawing, and game logic.
    """

    def __init__(self):
        """Set up the window, turtles, and event bindings."""

        # --- Window setup ---
        self.window = turtle.Screen()
        self.window.title(WINDOW_TITLE)
        self.window.bgcolor(BACKGROUND_COLOR)

        # Make the window big enough for the grid plus some padding for the score
        padding = 80
        window_width = (GRID_SIZE * SQUARE_SIZE) + padding
        window_height = (GRID_SIZE * SQUARE_SIZE) + padding + 40  # extra room for score
        self.window.setup(width=window_width, height=window_height)
        self.window.tracer(0)  # Turn off automatic screen updates (we update manually)

        # --- Create turtle objects for drawing ---

        # This turtle draws the background (border, grid lines)
        self.background_drawer = turtle.Turtle()
        self.background_drawer.hideturtle()
        self.background_drawer.penup()
        self.background_drawer.speed(0)

        # This turtle draws game objects (snake, apple, walls)
        self.game_drawer = turtle.Turtle()
        self.game_drawer.hideturtle()
        self.game_drawer.penup()
        self.game_drawer.speed(0)
        self.game_drawer.shape("square")
        # Make the square exactly SQUARE_SIZE pixels
        # Turtle's default square is 20x20, so we scale accordingly
        scale = SQUARE_SIZE / 20.0
        self.game_drawer.shapesize(scale, scale)

        # This turtle writes text (score, title, game over)
        self.text_drawer = turtle.Turtle()
        self.text_drawer.hideturtle()
        self.text_drawer.penup()
        self.text_drawer.speed(0)
        self.text_drawer.color(TEXT_COLOR)

        # --- Game state variables ---
        self.snake = []             # List of (column, row) positions; index 0 is the head
        self.direction = START_DIRECTION
        self.next_direction = START_DIRECTION  # Buffered direction to prevent 180-degree turns
        self.apple = (0, 0)         # (column, row) of the current apple
        self.walls = []             # List of (column, row) positions of wall blocks
        self.score = 0
        self.current_speed = STARTING_SPEED
        self.game_running = False
        self.game_over = False
        self.first_game = True      # The very first game has no walls
        self.timer_id = None        # Keeps track of the scheduled game tick

        # --- Draw the static background ---
        draw_border(self.background_drawer)
        draw_grid_lines(self.background_drawer)

        # --- Bind keyboard and mouse input ---
        self.bind_controls()

        # --- Show the title screen ---
        self.show_title_screen()
        self.window.update()

    # -------------------------------------------------------------------------
    # Input handling
    # -------------------------------------------------------------------------

    def bind_controls(self):
        """Connect keyboard and mouse events to game functions."""
        self.window.listen()

        # Arrow keys
        self.window.onkeypress(self.turn_up, "Up")
        self.window.onkeypress(self.turn_down, "Down")
        self.window.onkeypress(self.turn_left, "Left")
        self.window.onkeypress(self.turn_right, "Right")

        # WASD keys (mirrored controls)
        self.window.onkeypress(self.turn_up, "w")
        self.window.onkeypress(self.turn_down, "s")
        self.window.onkeypress(self.turn_left, "a")
        self.window.onkeypress(self.turn_right, "d")

        # Space to start or restart
        self.window.onkeypress(self.start_game, "space")

        # Click to start on the title screen
        self.window.onclick(self.on_click)

    def turn_up(self):
        """Change direction to up (but not if currently going down)."""
        if self.direction != "down":
            self.next_direction = "up"

    def turn_down(self):
        """Change direction to down (but not if currently going up)."""
        if self.direction != "up":
            self.next_direction = "down"

    def turn_left(self):
        """Change direction to left (but not if currently going right)."""
        if self.direction != "right":
            self.next_direction = "left"

    def turn_right(self):
        """Change direction to right (but not if currently going left)."""
        if self.direction != "left":
            self.next_direction = "right"

    def on_click(self, x, y):
        """Handle mouse clicks - used to start the game from the title screen."""
        if not self.game_running:
            self.start_game()

    # -------------------------------------------------------------------------
    # Game setup
    # -------------------------------------------------------------------------

    def start_game(self):
        """Begin a new game (or restart after game over)."""
        # Don't restart while a game is already running
        if self.game_running:
            return

        # Cancel any pending timer from a previous game
        if self.timer_id is not None:
            self.window.getcanvas().after_cancel(self.timer_id)
            self.timer_id = None

        # Reset game state
        self.score = 0
        self.current_speed = STARTING_SPEED
        self.direction = START_DIRECTION
        self.next_direction = START_DIRECTION
        self.game_running = True
        self.game_over = False

        # Build the snake at the starting position
        # The snake is a list of positions. Index 0 is the head.
        # The rest of the body trails behind to the left.
        self.snake = []
        for i in range(STARTING_LENGTH):
            segment_column = START_COLUMN - i
            segment_row = START_ROW
            self.snake.append((segment_column, segment_row))

        # Choose walls for this game
        if self.first_game:
            # First game is always a blank level (no walls)
            self.walls = []
            self.first_game = False
        else:
            # Pick a random wall layout from the list
            layout_string = random.choice(WALL_LAYOUTS)
            self.walls = parse_wall_layout(layout_string)

        # Place the first apple somewhere valid
        self.place_apple()

        # Start the game loop
        self.game_tick()

    def place_apple(self):
        """
        Place the apple in a random empty square.

        The apple cannot appear on the snake, on a wall, or outside the grid.
        """
        # Build a list of all empty squares
        empty_squares = []

        for column in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                position = (column, row)

                # Skip squares occupied by the snake
                if position in self.snake:
                    continue

                # Skip squares occupied by walls
                if position in self.walls:
                    continue

                # This square is empty, so it's a valid spot
                empty_squares.append(position)

        # Pick a random empty square for the apple
        if len(empty_squares) > 0:
            self.apple = random.choice(empty_squares)
        else:
            # The player has filled the entire board - they win!
            # (This is very unlikely but we handle it just in case.)
            self.apple = None

    # -------------------------------------------------------------------------
    # Main game loop
    # -------------------------------------------------------------------------

    def game_tick(self):
        """
        One step of the game. This is called repeatedly on a timer.
        Each tick, the snake moves forward one square.
        """
        if not self.game_running:
            return

        # Apply the buffered direction change
        self.direction = self.next_direction

        # Figure out where the head will move to
        head_column, head_row = self.snake[0]

        if self.direction == "up":
            new_head = (head_column, head_row - 1)
        elif self.direction == "down":
            new_head = (head_column, head_row + 1)
        elif self.direction == "left":
            new_head = (head_column - 1, head_row)
        elif self.direction == "right":
            new_head = (head_column + 1, head_row)

        # --- Check for collisions ---

        new_col, new_row = new_head

        # Check if the snake hit a wall (the border)
        if new_col < 0 or new_col >= GRID_SIZE or new_row < 0 or new_row >= GRID_SIZE:
            self.end_game()
            return

        # Check if the snake hit a wall block
        if new_head in self.walls:
            self.end_game()
            return

        # Check if the snake hit itself (but ignore the very last segment,
        # because it will move out of the way this tick unless we just ate)
        if new_head in self.snake:
            self.end_game()
            return

        # --- Move the snake ---

        # Add the new head position to the front of the snake list
        self.snake.insert(0, new_head)

        # Check if the snake ate the apple
        if new_head == self.apple:
            # Increase score
            self.score += 1

            # Speed up the game slightly
            self.current_speed = min(self.current_speed + SPEED_INCREASE, MAX_SPEED)

            # Place a new apple
            self.place_apple()
        else:
            # Remove the tail (the snake didn't grow this tick)
            self.snake.pop()

        # --- Draw everything ---
        self.draw_game()

        # --- Schedule the next tick ---
        # Convert speed (moves per second) to delay (milliseconds per move)
        delay_ms = int(1000 / self.current_speed)
        self.timer_id = self.window.getcanvas().after(delay_ms, self.game_tick)

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def draw_game(self):
        """Clear the game area and redraw the snake, apple, walls, and score."""
        # Clear previous drawings from the game turtle
        self.game_drawer.clearstamps()
        self.text_drawer.clear()

        # Draw the walls
        for wall_pos in self.walls:
            draw_square(self.game_drawer, wall_pos[0], wall_pos[1], WALL_COLOR)

        # Draw the apple (if it exists)
        if self.apple is not None:
            draw_square(self.game_drawer, self.apple[0], self.apple[1], APPLE_COLOR)

        # Draw the snake body (everything except the head)
        for segment in self.snake[1:]:
            draw_square(self.game_drawer, segment[0], segment[1], SNAKE_COLOR)

        # Draw the snake head in a slightly different color
        if len(self.snake) > 0:
            head = self.snake[0]
            draw_square(self.game_drawer, head[0], head[1], SNAKE_HEAD_COLOR)

        # Draw the score above the play area
        total_size = GRID_SIZE * SQUARE_SIZE
        score_y = (total_size // 2) + 15
        self.text_drawer.goto(0, score_y)
        self.text_drawer.color(SCORE_COLOR)
        self.text_drawer.write(
            f"Score: {self.score}",
            align="center",
            font=SCORE_FONT
        )

        # Update the screen to show all changes at once
        self.window.update()

    def show_title_screen(self):
        """Display the title screen with instructions."""
        self.text_drawer.clear()
        self.game_drawer.clearstamps()

        # Game title
        self.text_drawer.goto(0, 60)
        self.text_drawer.color(SNAKE_COLOR)
        self.text_drawer.write("SNAKE", align="center", font=TITLE_FONT)

        # Instructions
        self.text_drawer.goto(0, 10)
        self.text_drawer.color(TEXT_COLOR)
        self.text_drawer.write(
            "Eat the red apples to grow!",
            align="center",
            font=SUBTITLE_FONT
        )

        self.text_drawer.goto(0, -20)
        self.text_drawer.write(
            "Use Arrow Keys or WASD to move",
            align="center",
            font=SUBTITLE_FONT
        )

        self.text_drawer.goto(0, -70)
        self.text_drawer.color(APPLE_COLOR)
        self.text_drawer.write(
            "Click or press Space to start",
            align="center",
            font=SUBTITLE_FONT
        )

        self.window.update()

    def show_game_over_screen(self):
        """Display the game over message on top of the final game state."""
        # Draw the final state of the game so the player can see what happened
        self.draw_game()

        # "Game Over" text
        self.text_drawer.goto(0, 30)
        self.text_drawer.color(APPLE_COLOR)
        self.text_drawer.write("GAME OVER", align="center", font=GAME_OVER_FONT)

        # Final score
        self.text_drawer.goto(0, -10)
        self.text_drawer.color(TEXT_COLOR)
        self.text_drawer.write(
            f"Final Score: {self.score}",
            align="center",
            font=SUBTITLE_FONT
        )

        # Restart prompt
        self.text_drawer.goto(0, -50)
        self.text_drawer.write(
            "Press Space to play again",
            align="center",
            font=SUBTITLE_FONT
        )

        self.window.update()

    # -------------------------------------------------------------------------
    # Game over
    # -------------------------------------------------------------------------

    def end_game(self):
        """Handle the end of a game."""
        self.game_running = False
        self.game_over = True
        self.show_game_over_screen()

    # -------------------------------------------------------------------------
    # Run the game
    # -------------------------------------------------------------------------

    def run(self):
        """Start the turtle event loop. This keeps the window open."""
        self.window.mainloop()


# =============================================================================
# START THE GAME
# =============================================================================

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
