import random
from collections import deque

class GridWorld:
    def __init__(self, grid_size=(10, 10), wall_percentage=0.2):
        self.grid_size = grid_size
        self.wall_percentage = wall_percentage
        self.grid = [['empty' for _ in range(grid_size[1])] for _ in range(grid_size[0])]
        self.agent1_pos = self.random_position()
        self.agent2_pos = self.random_position(exclude=[self.agent1_pos])
        self.flag_pos = self.random_position(exclude=[self.agent1_pos, self.agent2_pos])
        self.turn = 0
        self.turns = 0
        self.scores = {1: 0, 2: 0}
        self.game_end_reason = None  # New: reason the game ended

        # Place walls
        self.place_walls()

    def random_position(self, exclude=[]):
        while True:
            x = random.randint(0, self.grid_size[0] - 1)
            y = random.randint(0, self.grid_size[1] - 1)
            if [x, y] not in exclude:
                return [x, y]

    def place_walls(self):
        num_walls = int(self.grid_size[0] * self.grid_size[1] * self.wall_percentage)
        walls = []

        for _ in range(num_walls):
            x, y = self.random_position(exclude=[self.agent1_pos, self.agent2_pos, self.flag_pos])
            walls.append((x, y))
            self.grid[x][y] = 'wall'

        if not self.is_connected():
            self.grid = [['empty' for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
            self.place_walls()
        else:
            self.walls = walls

    def is_connected(self):
        start = self.agent1_pos
        visited = set()
        queue = deque([start])
        visited.add(tuple(start))

        while queue:
            x, y = queue.popleft()
            for nx, ny in self.get_neighbors([x, y]):
                if self.grid[nx][ny] != 'wall' and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append([nx, ny])

        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                if self.grid[x][y] != 'wall' and (x, y) not in visited:
                    return False
        return True

    def get_neighbors(self, pos):
        x, y = pos
        neighbors = []
        if x > 0 and self.grid[x - 1][y] != 'wall':
            neighbors.append((x - 1, y))
        if x < self.grid_size[0] - 1 and self.grid[x + 1][y] != 'wall':
            neighbors.append((x + 1, y))
        if y > 0 and self.grid[x][y - 1] != 'wall':
            neighbors.append((x, y - 1))
        if y < self.grid_size[1] - 1 and self.grid[x][y + 1] != 'wall':
            neighbors.append((x, y + 1))
        return neighbors

    def get_state(self):
        return {
            'agent1_pos': self.agent1_pos,
            'agent2_pos': self.agent2_pos,
            'flag_pos': self.flag_pos,
            'turn': self.turn,
            'gridsize': self.grid_size
        }

    def get_adjacent_info(self, pos, agent_id):
        x, y = pos
        adjacent_info = {
            'up': self.get_tile_info(x - 1, y) if x > 0 else None,
            'down': self.get_tile_info(x + 1, y) if x < self.grid_size[0] - 1 else None,
            'left': self.get_tile_info(x, y - 1) if y > 0 else None,
            'right': self.get_tile_info(x, y + 1) if y < self.grid_size[1] - 1 else None
        }
        return adjacent_info

    def get_tile_info(self, x, y):
        if [x, y] == self.agent1_pos:
            return 'agent1'
        elif [x, y] == self.agent2_pos:
            return 'agent2'
        elif [x, y] == self.flag_pos:
            return 'flag'
        elif self.grid[x][y] == 'wall':
            return 'wall'
        else:
            return 'empty'

    def apply_action(self, agent, action):
        if agent == 1:
            pos = self.agent1_pos
            opponent_pos = self.agent2_pos
            opponent_id = 2
        else:
            pos = self.agent2_pos
            opponent_pos = self.agent1_pos
            opponent_id = 1

        original_pos = pos.copy()
        new_pos = pos.copy()
        moved = False

        if action == 'up':
            if pos[0] > 0 and self.grid[pos[0] - 1][pos[1]] != 'wall':
                new_pos[0] -= 1
                moved = True
        elif action == 'down':
            if pos[0] < self.grid_size[0] - 1 and self.grid[pos[0] + 1][pos[1]] != 'wall':
                new_pos[0] += 1
                moved = True
        elif action == 'left':
            if pos[1] > 0 and self.grid[pos[0]][pos[1] - 1] != 'wall':
                new_pos[1] -= 1
                moved = True
        elif action == 'right':
            if pos[1] < self.grid_size[1] - 1 and self.grid[pos[0]][pos[1] + 1] != 'wall':
                new_pos[1] += 1
                moved = True
        elif action == 'stay':
            self.scores[agent] -= 0.25
        else:
            #Passed invalid options
            self.scores[agent] -= 2

        #Not a valid move, walked into wall or off grid
        if action != 'stay' and not moved:
            self.scores[agent] -= 1.5

        if new_pos == opponent_pos:
            self.scores[opponent_id] += 5
            return

        if new_pos != original_pos:
            self.scores[agent] -= 1
            if agent == 1:
                self.agent1_pos = new_pos
            else:
                self.agent2_pos = new_pos

        if new_pos == self.flag_pos:
            self.scores[agent] += 50
            #self.game_end_reason = f"agent{agent} captured the flag"

    def is_stuck(self, agent_id):
        if agent_id == 1:
            x, y = self.agent1_pos
            opponent_pos = self.agent2_pos
        else:
            x, y = self.agent2_pos
            opponent_pos = self.agent1_pos

        directions = [
            (x - 1, y), (x + 1, y),
            (x, y - 1), (x, y + 1)
        ]

        for nx, ny in directions:
            if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]:
                if self.grid[nx][ny] != 'wall' and [nx, ny] != opponent_pos:
                    return False
        return True

    def is_game_over(self):
        if self.agent1_pos == self.flag_pos:
            self.game_end_reason = "Agent1 captured the flag"
            return True
        if self.agent2_pos == self.flag_pos:
            self.game_end_reason = "Agent2 captured the flag"
            return True

        if self.turns > 2 * self.grid_size[0] * self.grid_size[1]:
            self.game_end_reason = "Turn limit reached"
            return True

        if self.is_stuck(1):
            self.scores[2] += 100
            self.game_end_reason = "Agent1 is stuck"
            return True

        if self.is_stuck(2):
            self.scores[1] += 100
            self.game_end_reason = "Agent2 is stuck"
            return True

        return False

    def switch_turn(self):
        self.turn = 1 - self.turn
        if self.turn == 0:
            self.turns += 1


