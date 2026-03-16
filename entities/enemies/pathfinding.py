import itertools
import math
from heapq import heappush, heappop
from collections import deque

class PathfindingMixin:

    def _has_los(self, room, enemy_x, enemy_y, player_x, player_y):
        """Line-of-sight på GRID (Bresenham)."""
        dx = abs(player_x - enemy_x)
        dy = -abs(player_y - enemy_y)
        x_steps = 1 if enemy_x < player_x else -1
        y_steps = 1 if enemy_y < player_y else -1
        err = dx + dy

        x, y = enemy_x, enemy_y
        while True:
            if (x, y) != (enemy_x, enemy_y) and room.is_blocked(x, y):
                return False
            if x == player_x and y == player_y:
                return True 
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += x_steps
            if e2 <= dx:
                err += dx
                y += y_steps

    def _micro_wander(self, room, goal_g, max_depth):
        """BFS: finn NESTE grid-steg mot goal_g."""
        start = self._grid_pos()
        if start == goal_g:
            return None

        q = deque([start])
        came_from = {start: None}
        depth = {start: 0}
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while q:
            x, y = q.popleft()
            if (x, y) == goal_g:
                cur = (x, y)
                prev = came_from[cur]
                while prev and prev != start:
                    cur = prev
                    prev = came_from[cur]
                return cur

            if depth[(x, y)] >= max_depth:
                continue

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (nx, ny) in came_from:
                    continue
                if room.is_blocked(nx, ny):
                    continue
                came_from[(nx, ny)] = (x, y)
                depth[(nx, ny)] = depth[(x, y)] + 1
                q.append((nx, ny))

        return None

    def _astar_next_step(self, room, goal_g, max_expansions):
        start = self._grid_pos()
        
        if start == goal_g:
            return None
        if room.is_blocked(*goal_g) or room.is_blocked(*start):
            return None
        
        def h(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        openh = []
        counter = itertools.count()
        g_score = {start: 0}
        came_from = {start: None}
        
        f0 = h(start, goal_g)
        heappush(openh, (f0, 0, next(counter), start))
        
        closed = set()
        expansions = 0
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        best_node = start
        best_h = h(start, goal_g)
        
        while openh and expansions < max_expansions:
            _, _, _, current = heappop(openh)
            
            if current in closed:
                continue
            
            closed.add(current)
            expansions += 1
            
            if current == goal_g:
                return self._get_first_step(came_from, current, start)
            
            h_current = h(current, goal_g)
            if h_current < best_h:
                best_h = h_current
                best_node = current
            
            cx, cy = current
            for dx, dy in directions:
                neighbor = (cx + dx, cy + dy)
                
                if room.is_blocked(*neighbor):
                    continue
                
                tentative_g = g_score[current] + 1
                
                if tentative_g < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_val = h(neighbor, goal_g)
                    f_score = tentative_g + h_val
                    
                    heappush(openh, (f_score, h_val, next(counter), neighbor))
        
        if best_node != start:
            return self._get_first_step(came_from, best_node, start)
        
        return None