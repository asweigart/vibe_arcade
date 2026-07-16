"""
=============================================================================
  MAZE GAME - A Teaching Example
=============================================================================

This program demonstrates several programming concepts:
  - Maze generation using Wilson's algorithm with loop-erased random walks
  - Graph theory (the maze is a graph; paths between intersections are edges)
  - Pathfinding using Breadth-First Search (BFS) to ensure unique solutions
  - Game loop with Pygame
  - Event handling (keyboard input)

THE MAZE IS DRAWN AS LINES (not walls). Each cell-center can be connected to
its neighbors by a thin line. The player moves along these lines.

KEY FEATURE: Pressing an arrow key (or WASD) makes the player slide along
the path all the way to the next INTERSECTION (a junction with 3+ paths),
or to a dead end, or to the goal. This makes navigation feel snappy.

TELEPORTS: A few pairs of teleport pads are scattered through the maze.
Stepping onto one instantly moves you to its partner. Teleports are
considered when generating the maze, so they participate in the unique
solution path - they're a real shortcut, not a trick.

UNIQUE SOLUTION: We carefully ensure there is exactly ONE path from start
to goal, even taking teleports into account. This is what makes a "perfect"
maze actually solvable as a puzzle.
"""

import pygame      # The graphics/game library
import random      # For random maze generation
import sys         # For clean exit
from collections import deque  # deque is a fast queue, useful for BFS


# =============================================================================
# CONSTANTS - Tweak these to change the look and feel of the game!
# =============================================================================
# Try changing these values to experiment. Many interesting variations are
# possible by adjusting just a single number.

# ---- Maze Size ----
# The maze is a grid of CELLS. Each cell has a "center" point, and paths
# connect the centers of neighboring cells.
# EXPERIMENT: Make these bigger for a harder maze, smaller for an easier one.
# Very large mazes (e.g. 80x60) look beautiful but take longer to solve.
GRID_COLS = 60      # Number of cells horizontally
GRID_ROWS = 40      # Number of cells vertically

# ---- Cell Size (in pixels) ----
# This controls how big each cell appears on screen. Smaller = denser maze.
# EXPERIMENT: Try CELL_SIZE = 8 with a huge grid for a dramatic effect,
# or CELL_SIZE = 30 for a kid-friendly chunky maze.
CELL_SIZE = 14

# ---- Margin around the maze (pixels) ----
# Space between the maze edge and the window edge.
MARGIN = 20

# ---- Window Size (computed automatically from the values above) ----
# We add some extra height at the top for a status bar / instructions.
STATUS_BAR_HEIGHT = 40
WINDOW_WIDTH = GRID_COLS * CELL_SIZE + 2 * MARGIN
WINDOW_HEIGHT = GRID_ROWS * CELL_SIZE + 2 * MARGIN + STATUS_BAR_HEIGHT

# ---- Frame Rate ----
# How many times per second the screen redraws. 60 is smooth and standard.
FPS = 60

# ---- Colors (R, G, B) - each channel is 0-255 ----
# EXPERIMENT: Try a "blueprint" theme: BG=(20,40,80), PATH=(180,200,255).
# Or a "neon" theme: BG=(10,10,20), PATH=(255,80,200), PLAYER=(80,255,255).
COLOR_BG          = (24, 24, 32)     # Window background
COLOR_PATH        = (210, 215, 235)  # The maze path lines (bright, almost white)
COLOR_PATH_VISITED = (95, 100, 120)  # Already-traveled paths (dimmer)
COLOR_PLAYER      = (255, 220, 80)   # The player marker
COLOR_START       = (80, 200, 120)   # Green: the starting cell
COLOR_GOAL        = (220, 80, 80)    # Red: the goal cell
COLOR_TEXT        = (220, 220, 220)  # Status bar text
COLOR_WIN         = (255, 255, 120)  # Bright "you won!" color
# Teleport pad colors. We use a few distinct hues so each PAIR is recognizable.
# EXPERIMENT: Add more colors here AND increase NUM_TELEPORT_PAIRS to match.
TELEPORT_COLORS = [
    (120, 200, 255),  # cyan-blue
    (255, 160, 220),  # pink
    (200, 255, 140),  # lime
    (255, 180, 80),   # orange
]

# ---- Line Thickness ----
# How thick the path lines are drawn. Thicker = chunkier look.
LINE_THICKNESS = 2

# ---- Player Size ----
# Radius of the player's circle, in pixels.
PLAYER_RADIUS = max(3, CELL_SIZE // 3)

# ---- Animation Speed ----
# How fast the player slides along the path, in pixels per frame.
# At 60 FPS, a value of 4 means 240 pixels/sec - enough to feel snappy
# while still letting you SEE the player traverse a long corridor.
# EXPERIMENT: Set to 1 for slow-motion, 20 for near-instant teleport feel.
PLAYER_SPEED = 4

# ---- Teleports ----
# Each pair is two cells: stepping on one warps you to the other.
# EXPERIMENT: Set this to 0 for a classic maze with no teleports.
# Set it higher (up to len(TELEPORT_COLORS)) for more chaos.
NUM_TELEPORT_PAIRS = 0

# Radius of the teleport pad circle drawn at each teleport cell.
TELEPORT_RADIUS = max(3, CELL_SIZE // 3)

# ---- Start and Goal Positions ----
# (column, row). (0, 0) is top-left of the grid.
# By default we put start at top-left and goal at bottom-right.
START_CELL = (0, 0)
GOAL_CELL = (GRID_COLS - 1, GRID_ROWS - 1)


# =============================================================================
# MAZE GENERATION (Wilson's algorithm)
# =============================================================================
# Wilson's algorithm generates a "uniform spanning tree": every possible
# maze on this grid is EQUALLY LIKELY to be produced. Most maze algorithms
# (Kruskal's, Prim's, recursive backtracking) have subtle statistical biases
# - their mazes have a recognizable "fingerprint." Wilson's has no such
# bias. It is the gold standard for unbiased maze generation.
#
# THE IDEA: Build the maze incrementally by performing "loop-erased random
# walks" from cells not yet in the maze.
#
#   1) Pick any one cell and call it "in the maze." (Just a seed.)
#   2) Pick any cell NOT in the maze. From it, do a random walk: at each
#      step, move to a uniformly random neighbor. Keep walking until you
#      bump into a cell that IS in the maze.
#   3) Now ERASE LOOPS from your walk. If during the walk you visited the
#      same cell twice, snip out the loop in between - keep only the part
#      of the walk that doesn't revisit anything.
#   4) Add this loop-erased walk to the maze (its cells become "in", its
#      edges become real maze edges).
#   5) Repeat from step 2 until every cell is in the maze.
#
# WHY DOES IT WORK? It's a beautiful theorem: loop-erased random walks
# happen to sample edges in exactly the right way to make every spanning
# tree equally likely. This was proven by David Wilson in 1996.
#
# WHY THE EARLY WALKS ARE SLOW: When the "in the maze" set is tiny, a
# random walk has to wander a long time before it bumps into it. As the
# tree grows, walks finish faster and faster. So the algorithm starts
# slow but accelerates - opposite of most maze algorithms.

def generate_maze(cols, rows):
    """Return a set of edges. Each edge is a frozenset of two (col,row) cells."""
    # The set of cells already part of the maze ("in-tree" cells).
    in_tree = set()
    # The collection of edges we've decided to keep.
    edges = set()

    # Pick a random seed cell to start the tree.
    seed = (random.randrange(cols), random.randrange(rows))
    in_tree.add(seed)

    # All cells in some fixed order; we'll process them one by one and skip
    # any that already got pulled into the tree by an earlier walk.
    all_cells = [(c, r) for c in range(cols) for r in range(rows)]
    random.shuffle(all_cells)  # randomize order so the visual growth is even

    for start in all_cells:
        if start in in_tree:
            continue  # already absorbed by a previous walk

        # ----- Random walk with loop erasure -----
        # `path` is the current walk: a list of cells visited in order.
        # `path_index[cell]` gives the position in `path` where `cell` appears,
        # or is absent if `cell` isn't on the current walk. This lets us
        # detect loops in O(1) and erase them quickly.
        path = [start]
        path_index = {start: 0}

        cur = start
        while cur not in in_tree:
            # Step to a random neighbor (orthogonal, in-bounds).
            c, r = cur
            neighbors = []
            if c > 0:        neighbors.append((c - 1, r))
            if c + 1 < cols: neighbors.append((c + 1, r))
            if r > 0:        neighbors.append((c, r - 1))
            if r + 1 < rows: neighbors.append((c, r + 1))
            nxt = random.choice(neighbors)

            if nxt in path_index:
                # We've looped back onto our own walk! Snip out the loop:
                # erase everything in `path` after the previous occurrence.
                loop_start = path_index[nxt]
                # Remove the cells that were on the loop from path_index.
                for cell in path[loop_start + 1:]:
                    del path_index[cell]
                # Truncate the path back to the loop start (inclusive).
                del path[loop_start + 1:]
            else:
                # No loop: just extend the walk.
                path_index[nxt] = len(path)
                path.append(nxt)

            cur = nxt

        # ----- Walk hit the tree. Add it. -----
        # The walk now goes start -> ... -> some cell already in_tree.
        # Add every cell on the path to in_tree, and every consecutive pair
        # as an edge of the maze.
        for i in range(len(path) - 1):
            edges.add(frozenset((path[i], path[i + 1])))
            in_tree.add(path[i])
        # The last cell of `path` is in_tree already by construction (it was
        # the bumping-into point, or `cur` itself if the start was adjacent).
        in_tree.add(path[-1])

    return edges


# =============================================================================
# GRAPH HELPERS
# =============================================================================
# Once we have the maze edges, we build an adjacency list: for each cell,
# which cells can we step to directly? This is the graph the player walks.

def build_adjacency(edges):
    """Build cell -> list of neighbor cells from a set of edges."""
    adj = {}
    for edge in edges:
        a, b = tuple(edge)
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    return adj


def bfs_unique_path(adj, start, goal, teleports):
    """
    Breadth-First Search that ALSO uses teleports as edges.
    Returns (path_list, is_unique).

    `teleports` is a dict mapping cell -> partner cell. Stepping onto a
    teleport cell counts as also being at its partner (you arrive there
    automatically). We model this by adding the partner as an extra neighbor.

    BFS finds the SHORTEST path. To check uniqueness, we count how many
    distinct shortest paths there are; if more than one, it's not unique.
    For our purposes "unique solution" means there is exactly one shortest
    path from start to goal. Since the underlying maze is a tree, this is
    almost always true - but teleports can create alternative short routes,
    so we explicitly check.
    """
    # `dist[cell]` = shortest number of steps from start to cell
    dist = {start: 0}
    # `count[cell]` = number of distinct shortest paths from start to cell
    count = {start: 1}
    # `parent[cell]` = a previous cell on a shortest path (for reconstruction)
    parent = {start: None}

    queue = deque([start])
    while queue:
        u = queue.popleft()
        # Gather all places we could move to from u: adjacent cells AND, if u
        # is a teleport, its partner cell.
        neighbors = list(adj.get(u, []))
        if u in teleports:
            neighbors.append(teleports[u])

        for v in neighbors:
            if v not in dist:
                dist[v] = dist[u] + 1
                count[v] = count[u]
                parent[v] = u
                queue.append(v)
            elif dist[v] == dist[u] + 1:
                # Another equally-short way to reach v - solution not unique.
                count[v] += count[u]

    if goal not in dist:
        return None, False  # Goal unreachable (shouldn't happen with valid maze)

    # Rebuild a shortest path by walking parents back from goal.
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()

    is_unique = (count[goal] == 1)
    return path, is_unique


# =============================================================================
# TELEPORT PLACEMENT
# =============================================================================
# We pick random pairs of cells to be teleports, but we re-roll until the
# resulting maze has exactly ONE shortest solution. This guarantees the
# puzzle still has a single intended answer even with teleports active.
#
# Why might teleports break uniqueness? Imagine the natural maze path from
# start to goal takes 100 steps. If a teleport pair just happens to chain
# nicely with another route that ALSO takes 100 steps, then there are two
# equally-short solutions - so we'd reject that placement and try again.

def place_teleports(adj, start, goal, num_pairs, max_attempts=200):
    """Try random teleport placements until we find one with a unique solution."""
    cells = list(adj.keys())

    for attempt in range(max_attempts):
        # Pick num_pairs * 2 distinct cells, none of which are start or goal.
        # We exclude start/goal so the puzzle entry/exit don't get teleported.
        candidates = [c for c in cells if c != start and c != goal]
        # Need enough cells to make all the pairs we want.
        if len(candidates) < num_pairs * 2:
            return {}, []  # not enough room; no teleports

        chosen = random.sample(candidates, num_pairs * 2)

        # Build the teleport map: cell -> partner.
        teleports = {}
        pairs = []
        for i in range(num_pairs):
            a = chosen[2 * i]
            b = chosen[2 * i + 1]
            teleports[a] = b
            teleports[b] = a
            pairs.append((a, b))

        # Check that the maze still has a unique solution with these teleports.
        path, unique = bfs_unique_path(adj, start, goal, teleports)
        if unique and path is not None:
            return teleports, pairs

    # Fallback: no teleports if we couldn't find a working placement.
    # (Very unlikely with reasonable maze sizes.)
    return {}, []


# =============================================================================
# MOVEMENT: SLIDING TO THE NEXT INTERSECTION
# =============================================================================
# When the player presses an arrow key, we want them to slide along a corridor
# until they hit something interesting:
#   - An intersection (3+ neighbors): the player must choose a direction next.
#   - A dead end (1 neighbor, the way you came): you stop.
#   - The goal cell: you stop (you won!).
#   - A teleport: you stop AT the teleport, then warp on the NEXT step.
#     (That gives a moment to see the teleport before being whisked away.
#     EXPERIMENT: change this so the warp happens immediately during slide.)
#   - The start cell: you also stop here (treated as a special node).

def is_intersection(cell, adj, special_cells):
    """A cell is a 'stop here' point if it has 3+ exits, is a dead end's
    end, or is a special cell (start, goal, teleport)."""
    if cell in special_cells:
        return True
    return len(adj.get(cell, [])) >= 3


def slide(start_cell, direction, adj, special_cells):
    """
    Slide from start_cell in the given direction (dx, dy) until we hit a
    stopping point. Returns the full ROUTE as a list of cells, starting
    with start_cell and ending at the destination. If the player can't move
    at all, returns just [start_cell].

    Returning the whole route (not just the endpoint) lets us:
      - Animate the player along each segment smoothly.
      - Mark each edge we traverse as "visited" so we can dim it visually.

    The trick: after the first step, we follow the corridor by always going
    to the neighbor that ISN'T where we just came from. We stop when:
      - The current cell is "interesting" (intersection / special), OR
      - There's no unique forward neighbor (dead end).
    """
    dx, dy = direction
    target = (start_cell[0] + dx, start_cell[1] + dy)

    # First, can we even move one step in that direction?
    if target not in adj.get(start_cell, []):
        return [start_cell]  # blocked - no path that way

    route = [start_cell, target]
    prev = start_cell
    cur = target

    # Now slide forward through the corridor.
    while True:
        # If the current cell is special (intersection, start, goal, teleport),
        # stop here so the player can react.
        if is_intersection(cur, adj, special_cells):
            return route

        # Otherwise, find the one neighbor that isn't where we came from.
        neighbors = adj.get(cur, [])
        forward = [n for n in neighbors if n != prev]
        if len(forward) != 1:
            # Dead end (0 forward) or weird branch (shouldn't happen for non-
            # intersection cells, but handle defensively).
            return route

        # Step forward and keep going.
        prev = cur
        cur = forward[0]
        route.append(cur)


# =============================================================================
# DRAWING
# =============================================================================
# All rendering happens here. Pygame uses a coordinate system where (0,0) is
# the TOP-LEFT of the window, with y increasing DOWNWARD.

def cell_to_pixel(cell):
    """Convert a (col, row) grid cell to (x, y) pixel coordinates of its center."""
    c, r = cell
    x = MARGIN + c * CELL_SIZE + CELL_SIZE // 2
    y = MARGIN + STATUS_BAR_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2
    return x, y


def draw_maze(screen, edges, visited_edges, start, goal, teleport_pairs,
              player_pixel, won, font):
    """Draw the entire scene for one frame.

    `visited_edges` is a set of frozenset({a,b}) edges the player has already
    traversed; we draw those in a darker color.
    `player_pixel` is the (x, y) pixel position to draw the player at - this
    lets us animate smoothly between cells instead of jumping cell-to-cell.
    """
    # 1) Wipe the screen with the background color.
    screen.fill(COLOR_BG)

    # 2) Draw every edge of the maze as a line segment between cell centers.
    # Visited edges get the dimmer color; unvisited get the bright path color.
    for edge in edges:
        a, b = tuple(edge)
        color = COLOR_PATH_VISITED if edge in visited_edges else COLOR_PATH
        pygame.draw.line(
            screen, color,
            cell_to_pixel(a), cell_to_pixel(b),
            LINE_THICKNESS,
        )

    # 3) Draw the start and goal cells as colored circles.
    sx, sy = cell_to_pixel(start)
    gx, gy = cell_to_pixel(goal)
    pygame.draw.circle(screen, COLOR_START, (sx, sy), CELL_SIZE // 2)
    pygame.draw.circle(screen, COLOR_GOAL,  (gx, gy), CELL_SIZE // 2)

    # 4) Draw teleport pads. Each pair gets a unique color.
    # We draw both pads in the pair the same color so the player can see which
    # connects to which.
    for i, (a, b) in enumerate(teleport_pairs):
        color = TELEPORT_COLORS[i % len(TELEPORT_COLORS)]
        for cell in (a, b):
            cx, cy = cell_to_pixel(cell)
            # Outer ring then inner dot - just a touch of visual flair.
            pygame.draw.circle(screen, color, (cx, cy), TELEPORT_RADIUS)
            pygame.draw.circle(screen, COLOR_BG, (cx, cy), max(1, TELEPORT_RADIUS - 2))
            pygame.draw.circle(screen, color, (cx, cy), max(1, TELEPORT_RADIUS - 4))

    # 5) Draw the player on top of everything, at the given pixel position.
    px, py = player_pixel
    pygame.draw.circle(screen, COLOR_PLAYER, (int(px), int(py)), PLAYER_RADIUS)

    # 6) Draw the status bar at the top with instructions or a win message.
    if won:
        msg = "You reached the goal!  Press R for a new maze, ESC to quit."
        color = COLOR_WIN
    else:
        msg = "Arrow keys / WASD to move along paths.  R: new maze.  ESC: quit."
        color = COLOR_TEXT
    text_surface = font.render(msg, True, color)
    screen.blit(text_surface, (MARGIN, (STATUS_BAR_HEIGHT - text_surface.get_height()) // 2))


# =============================================================================
# THE MAIN GAME
# =============================================================================

def new_maze():
    """Generate a fresh maze + adjacency + teleports. Returns everything we need."""
    edges = generate_maze(GRID_COLS, GRID_ROWS)
    adj = build_adjacency(edges)
    teleports, pairs = place_teleports(adj, START_CELL, GOAL_CELL, NUM_TELEPORT_PAIRS)
    # special_cells are the cells where the slide-movement should STOP, even
    # if they aren't an intersection by branch count. Start/goal/teleports.
    special = {START_CELL, GOAL_CELL}
    special.update(teleports.keys())
    return edges, adj, teleports, pairs, special


def main():
    # Initialize pygame and create our window.
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Wilson Maze - slide through corridors!")
    clock = pygame.time.Clock()
    # A small font for the status bar. None means use the default system font.
    font = pygame.font.SysFont(None, 22)

    # Build the first maze.
    edges, adj, teleports, pairs, special = new_maze()
    player = START_CELL                    # Which cell the player logically occupies
    player_px = cell_to_pixel(player)      # Pixel position (for smooth animation)
    visited_edges = set()                  # Edges the player has crossed
    won = False

    # ----- Animation state -----
    # When the player presses a key, we compute the full route they'll slide
    # along, then animate one segment at a time. While animating, further
    # keypresses are ignored (it would be confusing to redirect mid-slide).
    #
    # `anim_route` is the list of cells in the slide route, e.g.
    #   [(0,0), (1,0), (2,0), (2,1)]
    # `anim_index` is the index of the cell we're currently moving TOWARDS,
    # so we're animating from anim_route[anim_index-1] to anim_route[anim_index].
    # When anim_index reaches len(anim_route), the slide is done.
    anim_route = None
    anim_index = 0

    # The mapping from key codes to (dx, dy) movement directions. We support
    # both arrow keys and WASD for convenience.
    # EXPERIMENT: add diagonal movement keys (this would also require building
    # diagonal edges in the maze - currently the maze is purely orthogonal).
    DIRECTIONS = {
        pygame.K_UP:    (0, -1),
        pygame.K_DOWN:  (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0),
        pygame.K_w:     (0, -1),
        pygame.K_s:     (0,  1),
        pygame.K_a:     (-1, 0),
        pygame.K_d:     (1,  0),
    }

    def reset():
        """Reset everything to a fresh maze. Defined as a closure so it can
        modify the variables we set up above."""
        nonlocal edges, adj, teleports, pairs, special
        nonlocal player, player_px, visited_edges, won, anim_route, anim_index
        edges, adj, teleports, pairs, special = new_maze()
        player = START_CELL
        player_px = cell_to_pixel(player)
        visited_edges = set()
        won = False
        anim_route = None
        anim_index = 0

    running = True
    while running:
        # ----- 1) HANDLE EVENTS -----
        # Pygame collects keyboard, mouse, and window events. We respond here.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_r:
                    reset()

                elif (not won
                      and anim_route is None         # not currently animating
                      and event.key in DIRECTIONS):
                    # The player wants to move. First check: are we currently
                    # standing on a teleport? If so, this keypress warps us.
                    # We do this BEFORE computing the slide so teleporting takes
                    # priority - one keypress = one teleport (otherwise sliding
                    # through a teleport could feel confusing).
                    if player in teleports:
                        player = teleports[player]
                        player_px = cell_to_pixel(player)
                        # Then we still let the keypress slide us from the
                        # destination, so movement feels responsive after warp.

                    direction = DIRECTIONS[event.key]
                    route = slide(player, direction, adj, special)

                    # Only start an animation if we actually moved somewhere.
                    if len(route) > 1:
                        anim_route = route
                        anim_index = 1   # heading toward route[1] from route[0]

        # ----- 2) UPDATE ANIMATION -----
        # If we're currently sliding, advance the player's pixel position by
        # PLAYER_SPEED toward the next cell. When we arrive, mark the edge we
        # just traversed as visited and either advance to the next segment or
        # finish the slide.
        if anim_route is not None:
            target_cell = anim_route[anim_index]
            tx, ty = cell_to_pixel(target_cell)
            # Vector from where we are to where we're going.
            cx, cy = player_px
            ddx = tx - cx
            ddy = ty - cy
            distance = (ddx * ddx + ddy * ddy) ** 0.5

            if distance <= PLAYER_SPEED:
                # We can reach the next cell this frame. Snap to it exactly.
                player_px = (tx, ty)
                # Mark the edge we just crossed as visited.
                prev_cell = anim_route[anim_index - 1]
                visited_edges.add(frozenset((prev_cell, target_cell)))
                # Player now logically occupies this cell.
                player = target_cell
                anim_index += 1

                # Done with the entire route?
                if anim_index >= len(anim_route):
                    anim_route = None
                    anim_index = 0
                    if player == GOAL_CELL:
                        won = True
            else:
                # Move PLAYER_SPEED pixels toward the target.
                # Normalize the direction vector and scale by PLAYER_SPEED.
                step_x = PLAYER_SPEED * ddx / distance
                step_y = PLAYER_SPEED * ddy / distance
                player_px = (cx + step_x, cy + step_y)

        # ----- 3) DRAW THE FRAME -----
        draw_maze(screen, edges, visited_edges, START_CELL, GOAL_CELL,
                  pairs, player_px, won, font)
        pygame.display.flip()  # Show the frame we just drew.

        # ----- 4) SLEEP UNTIL NEXT FRAME -----
        # tick(FPS) waits just long enough to maintain the desired frame rate.
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


# When this file is run directly (not imported), start the game.
if __name__ == "__main__":
    main()
