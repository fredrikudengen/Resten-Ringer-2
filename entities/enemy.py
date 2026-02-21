import itertools
import random
import math
from heapq import heappush, heappop

import pygame
from pygame.math import Vector2
from collections import deque

import constants
from .entity import Entity


class Enemy(Entity):

    def __init__(
        self, 
        x, y,
        speed=None,
        health=None,
        damage=None,
        detection_radius=None,
        attack_range=None,
        attack_cooldown=None,
        attack_windup_ms=None,      
        knockback_strength=None,
        size=None,
        color=None,
        wander_radius=None,
        xp_reward=None
    ):
            
        super().__init__(
            x, y,
            width=size[0],
            height=size[1],
            speed=speed,
            health=health,
            color=color
        )
        
        self.damage             = damage
        self.detection_radius   = detection_radius 
        self.attack_range       = attack_range
        self.attack_cooldown_ms = attack_cooldown
        self.attack_windup_ms   = attack_windup_ms
        self.knockback_strength = knockback_strength
        self.xp_reward          = xp_reward

        now = pygame.time.get_ticks()
        
        # Combat state
        self.hit_timer             = None
        self.attack_cooldown_until = 0
        self.attack_windup_until   = 0  

        # AI state machine
        self.state          = "idle"
        self.last_seen_pos  = None  
        self.search_started = None  

        # Micro-wander 
        self.wander_goal_g       = None
        self.wander_end          = False
        self.next_wander_at      = now + random.randint(1200, 2500)
        self.WANDER_INTERVAL_MS  = (1500, 2500) 
        self.WANDER_RADIUS_TILES = wander_radius 

    # ------------------------- PUBLIC API -------------------------

    def move(self, player, obstacles, room, dt_ms):
        """
        Oppdater fienden én frame: sansing, state-maskin, bevegelse.

        Args:
            player: objekt med .rect (pygame.Rect)
            obstacles: iterable av vegg-rektangler for kollisjon
            room: GridRoom med is_blocked(...) og TILE_SIZE
            dt_ms: millisekunder siden forrige frame
        """
        now = pygame.time.get_ticks()

        # Død short-circuit
        if self.health <= 0:
            self.alive         = False
            self.state         = "dead"
            self.wander_goal_g = None
            return

        # Treff / i-frames
        if self.hit:
            self.hit_timer      = now
            self.hit            = False
            self.last_seen_pos  = player.rect.center
            self.search_started = now
            self.state          = "search"
        
        if self.hit_timer and (now - self.hit_timer > 500):
            self.hit_timer = None

        # Sansing
        player_center = player.rect.center
        enemy_center  = self.rect.center
        see_player    = False
        
        dist2_to_player = self._dist2(*player_center, *enemy_center)
        if dist2_to_player <= self.detection_radius * self.detection_radius: 
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):                
                see_player          = True
                self.last_seen_pos  = player_center
                self.search_started = None

        # ---------------- State-maskin ----------------
        if self.state in ("idle", "walk", "hurt"):
            if see_player:
                self.state = "chase"
            else:
                self._idle(room, obstacles, dt_ms, now)

        elif self.state == "chase":
            self.wander_goal_g = None
            if see_player:
                if now >= self.attack_cooldown_until and self._dist2(*player_center, *enemy_center) <= (self.attack_range):
                    self.state = "attack"
                    self.attack_windup_until = now + self.attack_windup_ms
                else:
                    self._move_towards(player_center, obstacles, dt_ms)
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"
                    
        elif self.state == "attack":
            if now >= self.attack_windup_until:
                if dist2_to_player <= self.attack_range:
                    self._damage_player(player, self.damage)
                self.state = "chase"
                self.attack_cooldown_until = now + self.attack_cooldown_ms

        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now) 
            else:
                self.state = "idle"

        elif self.state == "dead":
            return
        
    def _idle(self, room, obstacles, dt_ms, now):
        """Håndter idle state med micro-wander."""
        if self.wander_goal_g is not None:
            next_tile_g = self._micro_wander(room, self.wander_goal_g, self.WANDER_RADIUS_TILES)
            if next_tile_g:
                target_px = self._center_of_tile(*next_tile_g)
                wander_end = self._move_towards(target_px, obstacles, dt_ms)
            else:
                wander_end = True  

            gx, gy = self._grid_pos()
                    
            if wander_end or (gx, gy) == self.wander_goal_g:
                self.wander_goal_g = None
                wait = random.randint(*self.WANDER_INTERVAL_MS)
                self.next_wander_at = now + wait
                        
        elif now >= self.next_wander_at:
            start_g = self._grid_pos()
            goal = self._pick_random_free_tile(room, start_g, self.WANDER_RADIUS_TILES)
            if goal and goal != start_g:
                self.wander_goal_g = goal
            else:
                wait = random.randint(*self.WANDER_INTERVAL_MS)
                self.next_wander_at = now + wait
    
    def _search(self, obstacles, room, dt_ms, now):
        """Håndter search state - gå til siste kjente posisjon."""
        T = constants.TILE_SIZE
        goal_g = (self.last_seen_pos[0] // T, self.last_seen_pos[1] // T)
        next_tile_g = self._astar_next_step(room, goal_g, max_expansions=512)
        if next_tile_g:
            target_px = self._center_of_tile(*next_tile_g)
            reached = self._move_towards(target_px, obstacles, dt_ms)
        else:
            reached = self._move_towards(self.last_seen_pos, obstacles, dt_ms)

        timedout = self.search_started and (now - self.search_started > constants.LOSE_SIGHT_TIME)
        if reached or timedout:
            self.state = "idle"
            self.last_seen_pos = None
            self.search_started = None  

    def draw(self, screen, camera):
        """
        Tegn fienden med fargekoding basert på state.
        Subklasser kan override for custom tegning.
        """
        draw_rect = camera.apply(self.rect)

        if self.state == "idle":
            color = self.color
        elif self.state == "chase":
            color = tuple(min(c + 40, 255) for c in self.color) 
        elif self.state == "search":
            color = tuple(max(c - 40, 0) for c in self.color)
        elif self.state == "attack":
            color = (255, 255, 255)
        elif self.state == "hurt":
            color = constants.RED
        elif self.state == "dead":
            color = (100, 100, 100)
        else:
            color = self.color

        pygame.draw.rect(screen, color, draw_rect)

    # ------------------------- INTERN LOGIKK -------------------------

    def _damage_player(self, player, amount):
        """
        Ta skade fra en kilde med knockback.
        Gjør ingenting hvis spilleren er invincible.

        Args:
            amount:     Mengde skade
            source_pos: (x, y) posisjon til angriperen – brukes for knockback-retning
        """
        if player.is_invincible:
            return

        player.health -= amount

        # Beregn knockback-retning bort fra kilden
        direction = pygame.math.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(1, 0)

        player.knockback_velocity = direction * self.knockback_strength

        # iframes
        player.hurt_invincible_until = pygame.time.get_ticks() + constants.PLAYER_HIT_INVINCIBLE_MS

        if player.health <= 0:
            player.alive = False
    
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

    def _slide_move(self, vx, vy, dt_ms, obstacles):
        """Smooth bevegelse med wall sliding."""
        dt = dt_ms / 1000.0
        dx_total = vx * dt
        dy_total = vy * dt
        steps = max(1, int(max(abs(dx_total), abs(dy_total)) // 4))
        sdx = dx_total / steps
        sdy = dy_total / steps
        
        for _ in range(steps):
            x_blocked = False
            y_blocked = False
            
            if sdx:
                self.pos.x += sdx
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.x -= sdx
                    self._sync_rect_from_pos()
                    x_blocked = True
            
            if sdy:
                self.pos.y += sdy
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.y -= sdy
                    self._sync_rect_from_pos()
                    y_blocked = True
            
            if x_blocked and not y_blocked and sdy:
                magnitude = (sdx**2 + sdy**2)**0.5
                self.pos.y += (magnitude - abs(sdy)) * (1 if sdy > 0 else -1)
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.y -= (magnitude - abs(sdy)) * (1 if sdy > 0 else -1)
                    self._sync_rect_from_pos()
            
            elif y_blocked and not x_blocked and sdx:
                magnitude = (sdx**2 + sdy**2)**0.5
                self.pos.x += (magnitude - abs(sdx)) * (1 if sdx > 0 else -1)
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.x -= (magnitude - abs(sdx)) * (1 if sdx > 0 else -1)
                    self._sync_rect_from_pos()

    def _move_towards(self, target_px, obstacles, dt_ms):
        """Gå mot en piksel-posisjon med normalisert fart."""
        direction = Vector2(target_px[0] - self.pos.x, target_px[1] - self.pos.y)
        dist = direction.length()
        if dist > 1e-6:
            direction /= dist
            self._slide_move(direction.x * self.speed, direction.y * self.speed, dt_ms, obstacles)
        return self._dist2(int(self.pos.x), int(self.pos.y), int(target_px[0]), int(target_px[1])) <= (24 * 24)
    
    def _apply_separation(self, others):
        """Myk dytting bort fra andre fiender."""
        strength = 0.08
        radius = 64
        self_x, self_y = self.pos.x, self.pos.y
        pushx = pushy = 0.0
        r2 = float(radius * radius)

        for other in others:
            if other is self or not other.alive:
                continue
            other_x, other_y = other.pos.x, other.pos.y
            distance_x, distance_y = self_x - other_x, self_y - other_y
            distance2 = distance_x * distance_x + distance_y * distance_y
            if 0 < distance2 < r2:
                weight = 1.0 / max(1.0, distance2)
                pushx += distance_x * weight
                pushy += distance_y * weight

        self.pos.x += pushx * strength
        self.pos.y += pushy * strength
        self._sync_rect_from_pos()

    def _pick_random_free_tile(self, room, center_g, radius):
        tries = 7
        cx, cy = center_g
        for _ in range(tries):
            nx = cx + random.randint(-radius, radius)
            ny = cy + random.randint(-radius, radius)
            if not room.is_blocked(nx, ny):
                return (nx, ny)
        return None

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

    def _get_first_step(self, came_from, node, start):
        path = []
        while node != start:
            path.append(node)
            node = came_from[node]
        return path[-1] if path else None
