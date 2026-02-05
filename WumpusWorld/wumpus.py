import random
import sys
import pygame
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
from collections import deque

GRID_SIZE = 4
CELL_PIT_PROB = 0.2
WINDOW_SCALE = 140
FPS = 30

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (210, 210, 210)
DARK_GRAY = (60, 60, 60)
RED = (200, 30, 30)
GREEN = (30, 160, 60)
BLUE = (30, 90, 200)
GOLD = (212, 175, 55)
PURPLE = (150, 60, 180)
BROWN = (139, 69, 19)

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
EAST, NORTH, WEST, SOUTH = 0, 1, 2, 3

@dataclass
class Percepts:
    breeze: bool = False
    stench: bool = False
    glitter: bool = False
    bump: bool = False
    scream: bool = False

@dataclass
class World:
    n: int = GRID_SIZE
    pits: Set[Tuple[int, int]] = field(default_factory=set)
    wumpus: Optional[Tuple[int, int]] = None
    gold: Optional[Tuple[int, int]] = None
    wumpus_alive: bool = True

    def inside(self, x: int, y: int) -> bool:
        return 1 <= x <= self.n and 1 <= y <= self.n

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        res = []
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if self.inside(nx, ny):
                res.append((nx, ny))
        return res

    def percepts_at(self, x: int, y: int, bump: bool = False, scream: bool = False) -> Percepts:
        breeze = any((nx, ny) in self.pits for nx, ny in self.neighbors(x, y))
        stench = self.wumpus_alive and any((nx, ny) == self.wumpus for nx, ny in self.neighbors(x, y))
        glitter = (x, y) == self.gold
        return Percepts(breeze=breeze, stench=stench, glitter=glitter, bump=bump, scream=scream)

    def reset_random(self):
        self.pits.clear()
        self.wumpus_alive = True
        self.wumpus = None
        self.gold = None
        for x in range(1, self.n + 1):
            for y in range(1, self.n + 1):
                if (x, y) == (1, 1):
                    continue
                if random.random() < CELL_PIT_PROB:
                    self.pits.add((x, y))
        while True:
            wx, wy = random.randint(1, self.n), random.randint(1, self.n)
            if (wx, wy) != (1, 1):  # allow Wumpus anywhere except start (even in a pit)
                self.wumpus = (wx, wy)
                break
        while True:
            gx, gy = random.randint(1, self.n), random.randint(1, self.n)
            if (gx, gy) != (1, 1):  # allow gold anywhere except start (even in a pit or on the Wumpus)
                self.gold = (gx, gy)
                break

@dataclass
class AgentState:
    x: int = 1
    y: int = 1
    dir: int = EAST
    has_gold: bool = False
    arrow_available: bool = True
    alive: bool = True

@dataclass
class Game:
    world: World = field(default_factory=World)
    agent: AgentState = field(default_factory=AgentState)
    score: int = 0
    terminal: bool = False
    last_scream: bool = False

    def reset(self):
        self.world.reset_random()
        self.agent = AgentState()
        self.score = 0
        self.terminal = False
        self.last_scream = False

    def turn_left(self):
        if self.terminal:
            return self.percepts()
        self.agent.dir = (self.agent.dir + 1) % 4
        self.score -= 1
        return self.percepts()

    def turn_right(self):
        if self.terminal:
            return self.percepts()
        self.agent.dir = (self.agent.dir - 1) % 4
        self.score -= 1
        return self.percepts()

    def move_forward(self):
        if self.terminal:
            return self.percepts()
        dx, dy = DIRS[self.agent.dir]
        nx, ny = self.agent.x + dx, self.agent.y + dy
        bump = False
        if not self.world.inside(nx, ny):
            bump = True
        else:
            self.agent.x, self.agent.y = nx, ny
            if (nx, ny) in self.world.pits:
                self.agent.alive = False
                self.terminal = True
                self.score -= 1
                self.score -= 1000
                return self.percepts()
            if self.world.wumpus_alive and (nx, ny) == self.world.wumpus:
                self.agent.alive = False
                self.terminal = True
                self.score -= 1
                self.score -= 1000
                return self.percepts()
        self.score -= 1
        return self.percepts(bump=bump)

    def grab(self):
        if self.terminal:
            return self.percepts()
        if (self.agent.x, self.agent.y) == self.world.gold and not self.agent.has_gold:
            self.agent.has_gold = True
            self.world.gold = None
        self.score -= 1
        return self.percepts()

    def release(self):
        if self.terminal:
            return self.percepts()
        if self.agent.has_gold:
            self.world.gold = (self.agent.x, self.agent.y)
            self.agent.has_gold = False
        self.score -= 1
        return self.percepts()

    def shoot(self):
        if self.terminal:
            return self.percepts()
        if not self.agent.arrow_available:
            self.score -= 1
            return self.percepts()
        self.agent.arrow_available = False
        self.score -= 10
        self.score -= 1
        x, y = self.agent.x, self.agent.y
        dx, dy = DIRS[self.agent.dir]
        while True:
            x += dx
            y += dy
            if not self.world.inside(x, y):
                break
            if self.world.wumpus_alive and (x, y) == self.world.wumpus:
                self.world.wumpus_alive = False
                self.last_scream = True
                break
        return self.percepts(scream=self.last_scream)

    def climb(self):
        if self.terminal:
            return self.percepts()
        if (self.agent.x, self.agent.y) == (1, 1):
            self.score -= 1
            if self.agent.has_gold:
                self.score += 1000
            self.terminal = True
        else:
            self.score -= 1
        return self.percepts()

    def percepts(self, bump: bool = False, scream: bool = False) -> Percepts:
        p = self.world.percepts_at(self.agent.x, self.agent.y, bump=bump, scream=scream or self.last_scream)
        self.last_scream = False
        return p

class Agent:
    def __init__(self, game: Game):
        self.game = game
        self.visited: Set[Tuple[int, int]] = set()
        self.path_home: List[str] = []
        self.safe: Set[Tuple[int, int]] = {(1, 1)}
        self.pits: Set[Tuple[int, int]] = set()
        self.wumpus_cell: Optional[Tuple[int, int]] = None
        self.breeze_cells: Set[Tuple[int, int]] = set()
        self.stench_cells: Set[Tuple[int, int]] = set()
        self.plan: List[str] = []

    def reset(self):
        self.visited.clear()
        self.path_home.clear()
        self.safe = {(1, 1)}
        self.pits.clear()
        self.wumpus_cell = None
        self.breeze_cells.clear()
        self.stench_cells.clear()
        self.plan.clear()

    def nbrs(self, x: int, y: int) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= self.game.world.n and 1 <= ny <= self.game.world.n:
                out.append((nx, ny))
        return out

    def update_knowledge(self, p: Percepts, x: int, y: int):
        if not p.breeze and not p.stench:
            for c in self.nbrs(x, y):
                if c not in self.pits:
                    self.safe.add(c)
        if p.breeze:
            self.breeze_cells.add((x, y))
            unknown = [c for c in self.nbrs(x, y) if c not in self.safe and c not in self.pits and c != self.wumpus_cell]
            if len(unknown) == 1:
                self.pits.add(unknown[0])
        if p.stench and self.game.world.wumpus_alive:
            self.stench_cells.add((x, y))
            unknown = [c for c in self.nbrs(x, y) if c not in self.safe and c not in self.pits]
            if self.wumpus_cell is None and len(unknown) == 1:
                self.wumpus_cell = unknown[0]
        self.infer_wumpus_from_intersections()

    def infer_wumpus_from_intersections(self):
        if self.wumpus_cell or not self.game.world.wumpus_alive:
            return
        candidates: Optional[Set[Tuple[int, int]]] = None
        for sx, sy in self.stench_cells:
            neigh = {c for c in self.nbrs(sx, sy) if c not in self.safe and c not in self.pits}
            candidates = neigh if candidates is None else candidates & neigh
            if not candidates:
                return
        if candidates and len(candidates) == 1:
            self.wumpus_cell = next(iter(candidates))

    def cell_risk(self, cell: Tuple[int, int]) -> float:
        if cell in self.safe or cell in self.pits:
            return 0.0 if cell in self.safe else 1.0
        if self.wumpus_cell and self.game.world.wumpus_alive and cell == self.wumpus_cell:
            return 1.0
        risk = 0.0
        for bx, by in self.breeze_cells:
            u = [c for c in self.nbrs(bx, by) if c not in self.safe and c not in self.pits]
            if cell in u and len(u) > 0:
                risk += 1.0 / len(u)
        return risk

    def best_adjacent_unknown(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        options = []
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not self.game.world.inside(nx, ny):
                continue
            c = (nx, ny)
            if c in self.visited or c in self.safe:
                continue
            if c in self.pits:
                continue
            if self.wumpus_cell and self.game.world.wumpus_alive and c == self.wumpus_cell:
                continue
            options.append((self.cell_risk(c), c))
        if not options:
            return None
        options.sort(key=lambda t: (t[0], t[1][0], t[1][1]))
        return options[0][1]

    def bfs_path(self, start: Tuple[int, int], goal_pred) -> List[str]:
        q = deque([(start, [], self.game.agent.dir)])
        seen = {(start, self.game.agent.dir)}
        while q:
            (cx, cy), path, cur_dir = q.popleft()
            if goal_pred((cx, cy)):
                return path
            for i, (dx, dy) in enumerate(DIRS):
                nx, ny = cx + dx, cy + dy
                if not self.game.world.inside(nx, ny):
                    continue
                nxt = (nx, ny)
                if nxt in self.pits:
                    continue
                if self.wumpus_cell and self.game.world.wumpus_alive and nxt == self.wumpus_cell:
                    continue
                if nxt not in self.safe:
                    continue
                need_dir = i
                turn = (need_dir - cur_dir) % 4
                if turn == 0:
                    step_seq = ["F"]
                elif turn == 1:
                    step_seq = ["L", "F"]
                elif turn == 3:
                    step_seq = ["R", "F"]
                else:
                    step_seq = ["L", "L", "F"]
                new_dir = need_dir
                state = (nxt, new_dir)
                if state in seen:
                    continue
                seen.add(state)
                q.append((nxt, path + step_seq, new_dir))
        return []

    def pick_safe_frontier(self) -> List[str]:
        frontier = [c for c in self.safe if c not in self.visited]
        if not frontier:
            return []
        start = (self.game.agent.x, self.game.agent.y)
        best = []
        for cell in frontier:
            path = self.bfs_path(start, lambda pos, cell=cell: pos == cell)
            if path and (not best or len(path) < len(best)):
                best = path
        return best

    def execute_action(self, a: str):
        if a == "F":
            self.game.move_forward()
        elif a == "L":
            self.game.turn_left()
        elif a == "R":
            self.game.turn_right()
        elif a == "C":
            self.game.climb()

    def wumpus_line_of_sight_guess(self) -> bool:
        if not self.wumpus_cell or not self.game.world.wumpus_alive:
            return False
        ax, ay = self.game.agent.x, self.game.agent.y
        wx, wy = self.wumpus_cell
        if ax == wx:
            desired = NORTH if wy > ay else SOUTH
            for y in range(ay + (1 if wy > ay else -1), wy, (1 if wy > ay else -1)):
                if (ax, y) in self.pits:
                    return False
            for t in self.turn_seq(self.game.agent.dir, desired):
                self.execute_action(t)
            self.game.shoot()
            return True
        if ay == wy:
            desired = EAST if wx > ax else WEST
            for x in range(ax + (1 if wx > ax else -1), wx, (1 if wx > ax else -1)):
                if (x, ay) in self.pits:
                    return False
            for t in self.turn_seq(self.game.agent.dir, desired):
                self.execute_action(t)
            self.game.shoot()
            return True
        return False

    def turn_seq(self, cur: int, target: int) -> List[str]:
        diff = (target - cur) % 4
        if diff == 0:
            return []
        if diff == 1:
            return ["L"]
        if diff == 3:
            return ["R"]
        return ["L", "L"]

    def danger_ahead(self, stench_now: bool) -> bool:
        dx, dy = DIRS[self.game.agent.dir]
        nx, ny = self.game.agent.x + dx, self.game.agent.y + dy
        if not self.game.world.inside(nx, ny):
            return False
        nxt = (nx, ny)
        if nxt in self.pits:
            return True
        if self.wumpus_cell and self.game.world.wumpus_alive and nxt == self.wumpus_cell:
            return True
        if stench_now and nxt not in self.safe:
            return True
        return False

    def step(self) -> bool:
        if self.game.terminal:
            return False
        x, y = self.game.agent.x, self.game.agent.y
        self.visited.add((x, y))
        p = self.game.percepts()
        self.update_knowledge(p, x, y)
        if p.glitter and not self.game.agent.has_gold:
            self.game.grab()
            self.plan = self.bfs_path((self.game.agent.x, self.game.agent.y), lambda pos: pos == (1, 1)) + ["C"]
            return True
        if (x, y) == (1, 1) and self.game.agent.has_gold:
            self.game.climb()
            return True
        if p.stench and self.game.agent.arrow_available:
            if self.wumpus_line_of_sight_guess():
                return True
            if self.danger_ahead(stench_now=True):
                self.game.shoot()
                return True
        if self.plan:
            a = self.plan.pop(0)
            self.execute_action(a)
            return True
        path = self.pick_safe_frontier()
        if path:
            self.plan = path
            a = self.plan.pop(0)
            self.execute_action(a)
            return True
        target = self.best_adjacent_unknown(x, y)
        if target and not p.stench:
            tx, ty = target
            for i, (dx, dy) in enumerate(DIRS):
                if (x + dx, y + dy) == (tx, ty):
                    for t in self.turn_seq(self.game.agent.dir, i):
                        self.execute_action(t)
                    self.game.move_forward()
                    return True
        if p.stench:
            if random.random() < 0.5:
                self.game.turn_left()
            else:
                self.game.turn_right()
            return True
        before = (self.game.agent.x, self.game.agent.y)
        p2 = self.game.move_forward()
        after = (self.game.agent.x, self.game.agent.y)
        if p2.bump or before == after:
            if random.random() < 0.5:
                self.game.turn_left()
            else:
                self.game.turn_right()
        return True

class Renderer:
    def __init__(self, game: Game):
        self.game = game
        pygame.init()
        self.font = pygame.font.SysFont("arial", 18)
        self.big = pygame.font.SysFont("arial", 22, bold=True)
        self.n = game.world.n
        w = self.n * WINDOW_SCALE
        h = self.n * WINDOW_SCALE + 80
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Wumpus World")
        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill(WHITE)
        self.draw_grid()
        self.draw_cells()
        self.draw_hud()
        pygame.display.flip()

    def grid_to_screen(self, x: int, y: int) -> Tuple[int, int, int, int]:
        cell = WINDOW_SCALE
        sx = (x - 1) * cell
        sy = (self.n - y) * cell
        return sx, sy, cell, cell

    def draw_grid(self):
        cell = WINDOW_SCALE
        for i in range(self.n + 1):
            pygame.draw.line(self.screen, GRAY, (i * cell, 0), (i * cell, self.n * cell), 1)
            pygame.draw.line(self.screen, GRAY, (0, i * cell), (self.n * cell, i * cell), 1)

    def draw_triangle(self, rect: Tuple[int, int, int, int], direction: int, color: Tuple[int, int, int]):
        x, y, w, h = rect
        cx = x + w // 2
        cy = y + h // 2
        size = min(w, h) // 3
        if direction == EAST:
            pts = [(cx - size, cy - size), (cx - size, cy + size), (cx + size, cy)]
        elif direction == WEST:
            pts = [(cx + size, cy - size), (cx + size, cy + size), (cx - size, cy)]
        elif direction == NORTH:
            pts = [(cx - size, cy + size), (cx + size, cy + size), (cx, cy - size)]
        else:
            pts = [(cx - size, cy - size), (cx + size, cy - size), (cx, cy + size)]
        pygame.draw.polygon(self.screen, color, pts)

    def draw_cells(self):
        for x in range(1, self.n + 1):
            for y in range(1, self.n + 1):
                rect = self.grid_to_screen(x, y)
                is_pit = (x, y) in self.game.world.pits
                is_wumpus = self.game.world.wumpus_alive and self.game.world.wumpus == (x, y)
                if not is_pit and not is_wumpus:
                    p = self.game.world.percepts_at(x, y)
                    if p.breeze:
                        pygame.draw.circle(self.screen, BLUE, (rect[0] + rect[2] - 20, rect[1] + 20), 8)
                    if p.stench:
                        pygame.draw.circle(self.screen, PURPLE, (rect[0] + 20, rect[1] + 20), 8)
                    if (x, y) == self.game.world.gold:
                        pygame.draw.circle(self.screen, GOLD, (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2), 10)
                else:
                    if (x, y) == self.game.world.gold:
                        pygame.draw.circle(self.screen, GOLD, (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2), 10)
        for (x, y) in self.game.world.pits:
            rect = self.grid_to_screen(x, y)
            pygame.draw.rect(self.screen, DARK_GRAY, (rect[0] + 10, rect[1] + 10, rect[2] - 20, rect[3] - 20), 2)
            txt = self.font.render("P", True, DARK_GRAY)
            self.screen.blit(txt, (rect[0] + 6, rect[1] + rect[3] - 24))
        if self.game.world.wumpus_alive and self.game.world.wumpus:
            wx, wy = self.game.world.wumpus
            rect = self.grid_to_screen(wx, wy)
            pygame.draw.rect(self.screen, RED, (rect[0] + 14, rect[1] + 14, rect[2] - 28, rect[3] - 28), 2)
            txt = self.font.render("W", True, RED)
            self.screen.blit(txt, (rect[0] + rect[2] - 24, rect[1] + rect[3] - 24))
        ax, ay = self.game.agent.x, self.game.agent.y
        rect = self.grid_to_screen(ax, ay)
        pygame.draw.rect(self.screen, GREEN, (rect[0] + 6, rect[1] + 6, rect[2] - 12, rect[3] - 12), 2)
        self.draw_triangle(rect, self.game.agent.dir, GREEN)
        if not self.game.agent.arrow_available:
            pygame.draw.line(self.screen, BROWN, (rect[0] + 8, rect[1] + rect[3] - 8), (rect[0] + rect[2] - 8, rect[1] + rect[3] - 8), 3)

    def draw_hud(self):
        y = self.n * WINDOW_SCALE + 8
        s1 = self.big.render(f"Score: {self.game.score}", True, BLACK)
        s2 = self.font.render(f"Gold: {'yes' if self.game.agent.has_gold else 'no'}  Arrow: {'yes' if self.game.agent.arrow_available else 'no'}  Alive: {'yes' if self.game.agent.alive else 'no'}", True, BLACK)
        s3_text = "Terminal: yes" if self.game.terminal else "Terminal: no"
        s3 = self.font.render(s3_text, True, RED if self.game.terminal else BLACK)
        help1 = self.font.render("Keys: R reset, N step, A auto-run, Q quit", True, BLACK)
        self.screen.blit(s1, (10, y))
        self.screen.blit(s2, (10, y + 26))
        self.screen.blit(s3, (10, y + 48))
        self.screen.blit(help1, (280, y + 26))


def auto_episode(game: Game, agent: Agent, renderer: Renderer):
    while not game.terminal:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        agent.step()
        renderer.draw()
        renderer.clock.tick(FPS)


def main():
    random.seed()
    game = Game()
    game.reset()
    agent = Agent(game)
    renderer = Renderer(game)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_r:
                    game.reset(); agent.reset()
                elif event.key == pygame.K_n:
                    agent.step()
                elif event.key == pygame.K_a:
                    auto_episode(game, agent, renderer)
        renderer.draw()
        renderer.clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()
