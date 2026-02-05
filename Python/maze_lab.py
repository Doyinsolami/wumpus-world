"""
COSC 581 - Lab 1
Generate a 21x21 maze, compute a valid path between random start and end,
and display the result with pygame:
- Start and end have unique colors
- Solution path has a unique color
- Visited cells that are not on the path have a unique color
Source: ChatGPT
"""

import sys
import random
from collections import deque
import pygame

# -----------------------------
# Grid and drawing parameters
# -----------------------------
GRID_SIZE = 21                  # Maze is 21 rows x 21 columns
CELL_SIZE = 24                  # Each cell is CELL_SIZE x CELL_SIZE pixels
WIDTH = GRID_SIZE * CELL_SIZE   # Window width in pixels
HEIGHT = GRID_SIZE * CELL_SIZE  # Window height in pixels

# -----------------------------
# Colors (RGB tuples)
# -----------------------------
COLOR_WALL    = (64, 64, 64)     # Walls
COLOR_OPEN    = (248, 249, 251)  # Passages
COLOR_BG      = (255, 255, 255)  # Window clear color
COLOR_EDGE    = (100, 100, 100)  # Outer border
COLOR_START   = (46, 204, 113)   # Start cell
COLOR_END     = (231, 76, 60)    # End cell
COLOR_VISITED = (180, 210, 255)  # Visited but not on final path
COLOR_PATH    = (255, 215, 0)    # Final path

# -----------------------------
# Maze generation
# -----------------------------
def make_full_wall_grid(n: int) -> list[list[int]]:
    """
    Create an n x n grid filled with 1.
    Convention: 1 means wall, 0 means open passage.
    """
    return [[1 for _ in range(n)] for _ in range(n)]

def generate_maze(n: int, rng: random.Random | None = None) -> list[list[int]]:
    """
    Generate a perfect maze using randomized DFS carving.
    We carve passages on odd coordinates and keep walls in between.
    Steps:
      1. Start from a random odd cell and mark it open.
      2. Use a stack to walk to neighboring odd cells, knocking down the wall between.
      3. Backtrack when there are no unvisited neighbors.
    """
    if rng is None:
        rng = random

    grid = make_full_wall_grid(n)

    # Pick a random odd starting cell inside the boundary
    r = rng.randrange(1, n, 2)
    c = rng.randrange(1, n, 2)
    grid[r][c] = 0  # open

    stack = [(r, c)]
    # Moves skip one cell to jump over a wall cell (2-step)
    dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]

    while stack:
        r, c = stack[-1]

        # Find candidate neighbors that are still walls two steps away
        neighbors = []
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 1 <= nr < n - 1 and 1 <= nc < n - 1 and grid[nr][nc] == 1:
                neighbors.append((nr, nc, dr, dc))

        if neighbors:
            # Choose one neighbor at random and carve toward it
            nr, nc, dr, dc = rng.choice(neighbors)
            wr, wc = r + dr // 2, c + dc // 2  # wall cell between current and neighbor
            grid[wr][wc] = 0                   # knock down wall
            grid[nr][nc] = 0                   # open neighbor
            stack.append((nr, nc))             # continue from the neighbor
        else:
            # Dead end, backtrack
            stack.pop()

    return grid

def random_open_cell(grid: list[list[int]], rng: random.Random | None = None) -> tuple[int, int]:
    """
    Return a random coordinate (row, col) where the cell is open (value 0).
    """
    if rng is None:
        rng = random
    opens = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 0]
    return rng.choice(opens)

# -----------------------------
# Pathfinding with BFS
# -----------------------------
def bfs_path(grid: list[list[int]],
             start: tuple[int, int],
             goal: tuple[int, int]) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    """
    Breadth-First Search on an unweighted grid.
    Returns:
      path: list of (row, col) from start to goal inclusive. Empty if not found.
      visited: set of all cells explored during the search.
    Reasoning:
      BFS guarantees a shortest path in number of steps on an unweighted grid.
    """
    n = len(grid)
    q = deque([start])      # frontier queue
    visited = {start}       # set of explored cells
    parent = {start: None}  # to rebuild the path
    moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # 4-connected grid

    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            # Reconstruct path by walking back through parents
            path: list[tuple[int, int]] = []
            cur = goal
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            return path, visited

        # Explore neighbors
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            # Inside bounds, open, and not yet visited
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0 and (nr, nc) not in visited:
                visited.add((nr, nc))
                parent[(nr, nc)] = (r, c)
                q.append((nr, nc))

    # Goal not reachable
    return [], visited

# -----------------------------
# Drawing the result with pygame
# -----------------------------
def draw(surface: pygame.Surface,
         grid: list[list[int]],
         start: tuple[int, int],
         goal: tuple[int, int],
         path: list[tuple[int, int]],
         visited: set[tuple[int, int]]) -> None:
    """
    Draw walls and openings, then overlay:
      - visited cells not on the final path
      - final path
      - start and goal cells
      - outer border
    """
    surface.fill(COLOR_BG)
    rows, cols = len(grid), len(grid[0])

    # Base maze cells
    for rr in range(rows):
        for cc in range(cols):
            rect = pygame.Rect(cc * CELL_SIZE, rr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if grid[rr][cc] == 1:
                pygame.draw.rect(surface, COLOR_WALL, rect)
            else:
                pygame.draw.rect(surface, COLOR_OPEN, rect)

    # Visited but not on the final path
    path_set = set(path)
    for (vr, vc) in (visited - path_set):
        rect = pygame.Rect(vc * CELL_SIZE, vr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, COLOR_VISITED, rect)

    # Final path
    for (pr, pc) in path:
        rect = pygame.Rect(pc * CELL_SIZE, pr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, COLOR_PATH, rect)

    # Start and goal
    sr, sc = start
    er, ec = goal
    srect = pygame.Rect(sc * CELL_SIZE, sr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    erect = pygame.Rect(ec * CELL_SIZE, er * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, COLOR_START, srect)
    pygame.draw.rect(surface, COLOR_END, erect)

    # Border
    pygame.draw.rect(surface, COLOR_EDGE, pygame.Rect(0, 0, WIDTH, HEIGHT), 2)

# -----------------------------
# Main program
# -----------------------------
def main() -> None:
    """
    Create the window, generate a maze, pick random start and end,
    compute a valid path with BFS, and display.
    Controls:
      R regenerates a new maze and re-runs BFS
      Q quits
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("COSC 581 - Lab 1 Maze")
    clock = pygame.time.Clock()
    rng = random.Random()

    # First maze and path
    grid = generate_maze(GRID_SIZE, rng)
    start = random_open_cell(grid, rng)
    goal = random_open_cell(grid, rng)
    while goal == start:
        goal = random_open_cell(grid, rng)
    path, visited = bfs_path(grid, start, goal)

    # If somehow no path was found, try a few more times
    tries = 0
    while not path and tries < 5:
        grid = generate_maze(GRID_SIZE, rng)
        start = random_open_cell(grid, rng)
        goal = random_open_cell(grid, rng)
        while goal == start:
            goal = random_open_cell(grid, rng)
        path, visited = bfs_path(grid, start, goal)
        tries += 1

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    # New maze and new random endpoints
                    grid = generate_maze(GRID_SIZE, rng)
                    start = random_open_cell(grid, rng)
                    goal = random_open_cell(grid, rng)
                    while goal == start:
                        goal = random_open_cell(grid, rng)
                    path, visited = bfs_path(grid, start, goal)

        # Draw the current state
        draw(screen, grid, start, goal, path, visited)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
