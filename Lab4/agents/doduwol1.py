"""
COSC 581 - Lab 4
Capture-the-flag agent for a 10x10 grid world:
- Implements the Agent interface from base_agent.py
- Chooses actions from: "up", "down", "left", "right", "stay"
- World contains random walls, two agents, and one flag
- Agent should explore, avoid invalid moves and collisions, and try to capture the flag while minimizing score penalties
Source: ChatGPT
"""

from base_agent import Agent as BaseAgent
from collections import deque
import heapq

class Agent(BaseAgent):
    def __init__(self):
        self.GRID_SIZE = 10
        self.map = [['unknown' for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        self.visited = {}
        self.history = deque(maxlen=6)
        self.recent = deque(maxlen=12)
        self.last_dir = None
        self.flag_pos = None

    def _dir_to_delta(self, d):
        return {'up':(-1,0),'right':(0,1),'down':(1,0),'left':(0,-1)}[d]

    def _next(self, pos, d):
        dr, dc = self._dir_to_delta(d)
        return (pos[0]+dr, pos[1]+dc)

    def _reverse(self, d):
        return {'up':'down','down':'up','left':'right','right':'left'}[d]

    def _norm(self, v):
        if isinstance(v, dict):
            for k in ('type','value','cell','content','kind','label'):
                if k in v:
                    v = v[k]
                    break
        if v is None:
            return 'wall'
        s = str(v).strip().lower()
        if s in ('flag','f'): return 'flag'
        if s in ('wall','#','w'): return 'wall'
        if s in ('agent1','a1'): return 'agent1'
        if s in ('agent2','a2'): return 'agent2'
        if s in ('none','empty','0',''): return 'empty'
        return s

    def _set_map(self, pos, value):
        r, c = pos
        if 0 <= r < self.GRID_SIZE and 0 <= c < self.GRID_SIZE:
            self.map[r][c] = value

    def _get_map(self, pos):
        r, c = pos
        if 0 <= r < self.GRID_SIZE and 0 <= c < self.GRID_SIZE:
            return self.map[r][c]
        return 'wall'

    def _update_map(self, pos, adj):
        self._set_map(pos, 'empty')
        for d in ('up','right','down','left'):
            dr, dc = self._dir_to_delta(d)
            r, c = pos[0]+dr, pos[1]+dc
            if 0 <= r < self.GRID_SIZE and 0 <= c < self.GRID_SIZE:
                val = self._norm(adj.get(d))
                self._set_map((r, c), val)
                if val == 'flag':
                    self.flag_pos = (r, c)

    def _neighbors_known_passable(self, pos):
        for d in ('up','right','down','left'):
            npos = self._next(pos, d)
            if self._get_map(npos) not in ('wall','agent1','agent2'):
                yield npos, d

    def _dir_to(self, a, b):
        dr = b[0] - a[0]
        dc = b[1] - a[1]
        if dr == -1 and dc == 0: return 'up'
        if dr == 1 and dc == 0:  return 'down'
        if dr == 0 and dc == -1: return 'left'
        if dr == 0 and dc == 1:  return 'right'
        return None

    def _h(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def _astar_first_step(self, start, goal):
        pq = [(0, start)]
        came = {start: None}
        g = {start: 0}
        while pq:
            _, cur = heapq.heappop(pq)
            if cur == goal:
                break
            for npos, _ in self._neighbors_known_passable(cur):
                ng = g[cur] + 1
                if npos not in g or ng < g[npos]:
                    g[npos] = ng
                    heapq.heappush(pq, (ng + self._h(npos, goal), npos))
                    came[npos] = cur
        if goal not in came:
            return None
        node = goal
        while came[node] and came[node] != start:
            node = came[node]
        return self._dir_to(start, node)

    def _bfs_first_step_to_nearest_unknown(self, start):
        from collections import deque as _dq
        q = _dq([start])
        came = {start: None}
        target = None

        def is_frontier(p):
            if self._get_map(p) == 'unknown':
                return True
            for d in ('up','right','down','left'):
                if self._get_map(self._next(p, d)) == 'unknown':
                    return True
            return False

        if is_frontier(start):
            target = start
        else:
            while q:
                cur = q.popleft()
                for npos, _ in self._neighbors_known_passable(cur):
                    if npos in came:
                        continue
                    came[npos] = cur
                    if is_frontier(npos):
                        target = npos
                        q.appendleft(npos)
                        q.clear()
                        break
                    q.append(npos)

        if not target:
            return None

        node = target
        while came[node] and came[node] != start:
            node = came[node]
        return self._dir_to(start, node)

    def get_action(self, state, agent_id):
        pos = tuple(state['agent1_pos'] if agent_id == 1 else state['agent2_pos'])
        other_key = 'agent2' if agent_id == 1 else 'agent1'
        adj = state.get('adjacent_info', {})

        # learn first
        self._update_map(pos, adj)

        # capture if neighbor is flag
        for d in ('up','right','down','left'):
            if self._norm(adj.get(d)) == 'flag':
                self.last_dir = d
                return d

        
        self.visited[pos] = self.visited.get(pos, 0) + 1
        self.history.append(pos)
        self.recent.append(pos)

        
        def is_safe_dir(d):
            cell = self._norm(adj.get(d))
            return cell not in ('wall', other_key, None)

        # if flag is known, A* toward it, but only step if the chosen step is safe now
        if self.flag_pos:
            step = self._astar_first_step(pos, self.flag_pos)
            if step and is_safe_dir(step):
                self.last_dir = step
                return step

        # prefer any adjacent unknown now
        for d in ('up','right','down','left'):
            npos = self._next(pos, d)
            if is_safe_dir(d) and self._get_map(npos) == 'unknown':
                self.last_dir = d
                return d

        # otherwise BFS to nearest unknown frontier and take its first step if safe
        step_to_unknown = self._bfs_first_step_to_nearest_unknown(pos)
        if step_to_unknown and is_safe_dir(step_to_unknown):
            self.last_dir = step_to_unknown
            return step_to_unknown

        # final fallback, choose least visited safe neighbor, avoid immediate reverse if possible
        safe_dirs = [d for d in ('up','right','down','left') if is_safe_dir(d)]
        if not safe_dirs:
            self.last_dir = None
            return 'stay'

        nonrev = [d for d in safe_dirs if d != self._reverse(self.last_dir)] or safe_dirs
        pri = {'up':0,'right':1,'down':2,'left':3}
        best = min(nonrev, key=lambda d: (self.visited.get(self._next(pos, d), 0), pri[d]))
        self.last_dir = best
        return best
