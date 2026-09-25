import random

import pygame

from src.core import constants, debug
from src.entities.entity import Entity
from src.entities.enemies.pathfinding import PathfindingMixin
from src.entities.enemies.movement import MovementMixin


class Enemy(PathfindingMixin, MovementMixin, Entity):

    detection_radius = 0  # px; None = alltid oppdaget (se ScoutEnemy)

    def __init__(self, x, y):

        super().__init__(x, y)

        self.max_health = self.health

        now = pygame.time.get_ticks()
        
        self.alive                 = True
        self.hit                   = False
        self.attack_cooldown_until = 0

        self.state          = "idle"
        self.last_seen_pos  = None
        self.search_started = None
        self._debug_los     = None

        self.wander_goal_g       = None
        self.wander_end          = False
        self.next_wander_at      = now + random.randint(1200, 2500)
        self.WANDER_INTERVAL_MS  = (1500, 2500)
        self.wander_radius       = 4

        self.facing_left         = False

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
        prev_x = self.pos.x

        if self.health <= 0:
            self.alive         = False
            self.state         = "dead"
            self.wander_goal_g = None
            return

        if self.hit and self.state not in ("attack", "chase"):
            self.hit            = False
            self.last_seen_pos  = player.rect.center
            self.search_started = now
            self.state          = "search"

        player_center = player.rect.center
        enemy_center  = self.rect.center
        see_player    = False
        
        self._debug_los = None
        dist2_to_player = self._dist2(*player_center, *enemy_center)
        if dist2_to_player <= self.detection_radius * self.detection_radius:
            self._debug_los = player_center
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):
                see_player          = True
                self.last_seen_pos  = player_center
                self.search_started = None

        self.update_knockback(obstacles)

        if self.state in ("idle", "walk"):
            if see_player:
                self.state = "chase"
            else:
                self._idle(room, obstacles, dt_ms, now)

        elif self.state == "chase":
            self.wander_goal_g = None
            if see_player:
                self._move_towards(player_center, obstacles, dt_ms)
                if now >= self.attack_cooldown_until and self.rect.colliderect(player.rect):
                    self._damage_player(player, self.damage)
                    self.attack_cooldown_until = now + self.attack_cooldown
                    self.apply_knockback(player.rect, 16)  # liten self-knockback
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"

        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now) 
            else:
                self.state = "idle"

        elif self.state == "dead":
            return

        dx = self.pos.x - prev_x
        if abs(dx) > 1e-3:
            self.facing_left = dx < 0

    def _sprite_frame(self) -> str:
        return "idle"

    def _is_moving(self) -> bool:
        return self.state == "chase" or self.state == "search" or (
            self.state == "idle" and self.wander_goal_g is not None
        )

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        # if self.state == "idle":
        #     color = self.color
        # elif self.state == "chase":
        #     color = tuple(min(c + 40, 255) for c in self.color)
        # elif self.state == "search":
        #     color = tuple(max(c - 40, 0) for c in self.color)
        # elif self.state == "attack":
        #     color = (255, 255, 255)
        # elif self.state == "dead":
        #     color = (100, 100, 100)
        # else:
        #     color = self.color

        self.sprite.draw(
            screen, draw_rect, frame=self._sprite_frame(),
            flip_x=self.facing_left, moving=self._is_moving()
        )
        self._draw_healthbar(screen, camera)

        if self.state in ("idle", "walk") and self.wander_goal_g is not None:
            debug.draw_tile(screen, camera, self.wander_goal_g)

        if self._debug_los is not None:
            debug.draw_line(screen, camera, self.rect.center, self._debug_los)

        if self.detection_radius is not None:
            debug.draw_circle(screen, camera, self.rect.center, self.detection_radius)
        debug.draw_label(screen, camera, (self.rect.centerx, self.rect.top - 20), self.state)

    def _draw_healthbar(self, screen, camera):
        """Liten helsebar over fienden. Skjult ved full helse."""
        if not self.alive or self.health <= 0 or self.health >= self.max_health:
            return

        ratio = max(0.0, min(1.0, self.health / self.max_health))

        draw_rect = camera.apply(self.rect)
        border = 2
        bar_w  = draw_rect.width
        bar_h  = 8
        bar_x  = draw_rect.x
        bar_y  = draw_rect.top - bar_h - 8

        outer = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        inner = outer.inflate(-border * 2, -border * 2)

        filled_w  = int(inner.width * ratio)
        red_rect  = pygame.Rect(inner.x, inner.y, filled_w, inner.height)
        grey_rect = pygame.Rect(inner.x + filled_w, inner.y, inner.width - filled_w, inner.height)

        if red_rect.width > 0:
            pygame.draw.rect(screen, (200, 40, 40), red_rect)
        if grey_rect.width > 0:
            pygame.draw.rect(screen, (110, 110, 110), grey_rect)
        pygame.draw.rect(screen, (255, 255, 255), outer, border)

    # ---------- HELPERS ----------
        
    def _idle(self, room, obstacles, dt_ms, now):
        """Håndter idle state med micro-wander."""
        if self.wander_goal_g is not None:
            next_tile_g = self._micro_wander(room, self.wander_goal_g, self.wander_radius)
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
            goal = self._pick_random_free_tile(room, start_g, self.wander_radius)
            if goal and goal != start_g:
                self.wander_goal_g = goal
            else:
                wait = random.randint(*self.WANDER_INTERVAL_MS)
                self.next_wander_at = now + wait
    
    def _search(self, obstacles, room, dt_ms, now):
        """Håndter search state. Gå mot siste kjente posisjon."""
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

    def _damage_player(self, player, amount):

        if player.is_invincible:
            return

        player.health -= int(amount)

        for relic in player.relics:
            relic.on_hit(player)

        player.apply_knockback(self.rect, self.knockback_strength)

        # iframes
        player.hurt_invincible_until = pygame.time.get_ticks() + constants.PLAYER_HIT_INVINCIBLE_MS

        if player.health <= 0:
            player.alive = False

    def _pick_random_free_tile(self, room, center_g, radius):
        """
        Velg en tilfeldig fri tile.

        Args:
            center_g: grid posisjon start
            radius: radius i tiles
        """
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