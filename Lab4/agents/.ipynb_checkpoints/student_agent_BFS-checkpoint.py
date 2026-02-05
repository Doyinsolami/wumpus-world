

from base_agent import Agent
from collections import deque
import random

class Agent(Agent):
    def __init__(self):
        super().__init__()
        self.visited = set()
        self.grid_size = (5, 5)
        self.path = []
        self.known_walls = set()

    def get_action(self, state, agent_id):
        if agent_id == 1:
            my_pos = tuple(state['agent1_pos'])
            opp_pos = tuple(state['agent2_pos'])
        else:
            my_pos = tuple(state['agent2_pos'])
            opp_pos = tuple(state['agent1_pos'])

        self.grid_size = state['gridsize']
        self.visited.add(my_pos)
        self.current_pos = my_pos

        adjacent_info = state.get('adjacent_info', {})

        # Learn about walls in adjacent tiles
        self.update_known_walls(my_pos, adjacent_info)

        # Move to flag if adjacent
        for direction, info in adjacent_info.items():
            if info == 'flag':
                return direction

        # Plan new path if needed
        if not self.path:
            self.path = self.bfs_explore(my_pos, opp_pos)

        # Follow the path
        if self.path:
            next_pos = self.path.pop(0)
            return self.direction_to_move(my_pos, next_pos)

        # Fallback: random unvisited direction
        return self.move_randomly(adjacent_info)

    def update_known_walls(self, pos, adjacent_info):
        """Store walls based on adjacent perception."""
        deltas = {
            'up': (-1, 0),
            'down': (1, 0),
            'left': (0, -1),
            'right': (0, 1)
        }

        for direction, tile in adjacent_info.items():
            if tile == 'wall':
                dx, dy = deltas[direction]
                wall_pos = (pos[0] + dx, pos[1] + dy)
                self.known_walls.add(wall_pos)

    def bfs_explore(self, start, opponent_pos):
        """Breadth-First Search avoiding known walls and visited tiles."""
        queue = deque([(start, [])])
        visited_in_bfs = set([start])

        while queue:
            current_pos, path = queue.popleft()
            for neighbor in self.get_neighbors(current_pos):
                if neighbor in visited_in_bfs or neighbor == opponent_pos:
                    continue
                visited_in_bfs.add(neighbor)
                new_path = path + [neighbor]
                if neighbor not in self.visited:
                    return new_path
                queue.append((neighbor, new_path))
        return []

    def get_neighbors(self, pos):
        """Return in-bounds neighbors that are not known walls."""
        x, y = pos
        potential = [
            (x - 1, y), (x + 1, y),
            (x, y - 1), (x, y + 1)
        ]
        neighbors = [
            (nx, ny) for nx, ny in potential
            if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]
            and (nx, ny) not in self.known_walls
        ]
        return neighbors

    def direction_to_move(self, current, target):
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        if dx == -1: return 'up'
        if dx == 1: return 'down'
        if dy == -1: return 'left'
        if dy == 1: return 'right'
        return 'stay'

    def move_randomly(self, adjacent_info):
        direction_deltas = {
            'up': (-1, 0),
            'down': (1, 0),
            'left': (0, -1),
            'right': (0, 1)
        }

        x, y = self.current_pos
        options = []

        for direction, delta in direction_deltas.items():
            if adjacent_info.get(direction) == 'empty':
                dx, dy = delta
                new_pos = (x + dx, y + dy)
                if new_pos not in self.visited and new_pos not in self.known_walls:
                    options.append(direction)

        return random.choice(options) if options else 'stay'
