import itertools
import random
import math

import pygame
from pygame.math import Vector2
from core import constants

from ..entity import Entity
from .pathfinding import PathfindingMixin
from .movement import MovementMixin


class Enemy(PathfindingMixin, MovementMixin, Entity):

    def __init__(self, x, y):

        super().__init__(x, y)       

        now = pygame.time.get_ticks()
        
        # Combat state
        self.alive                 = True
        self.hit                   = False
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
        self.wander_radius       = 4
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
                self.attack_cooldown_until = now + self.attack_cooldown

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

    def _pick_random_free_tile(self, room, center_g, radius):
        tries = 7
        cx, cy = center_g
        for _ in range(tries):
            nx = cx + random.randint(-radius, radius)
            ny = cy + random.randint(-radius, radius)
            if not room.is_blocked(nx, ny):
                return (nx, ny)
        return None

    def _get_first_step(self, came_from, node, start):
        path = []
        while node != start:
            path.append(node)
            node = came_from[node]
        return path[-1] if path else None
