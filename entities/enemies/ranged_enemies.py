from __future__ import annotations

import math
import random

import pygame
from pygame.math import Vector2

from core import constants
from .enemy import Enemy

from components.gun import EnemyPistol, EnemyRifle


class RangedEnemy(Enemy):
    """
    Base class for enemies that shoot projectiles at the player.

    Subclass attributes to override
    --------------------------------
    gun_class          : Gun subclass to equip (default EnemyPistol)
    preferred_range_px : Ideal pixel distance to player while shooting (default 300)
    min_range_px       : Won't advance closer than this (default 140)
    reposition_interval: ms between LOS-position searches while chasing (default 800)
    """

    # ---- override these in subclasses ----
    gun_class:            type  = EnemyPistol
    preferred_range_px:   int   = 300
    min_range_px:         int   = 140
    reposition_interval:  int   = 800    # ms between reposition searches

    # ---- sensible defaults (subclass can still override) ----
    speed            = 100
    health           = 70
    damage           = 0          # ranged enemies don't melee — kept for compat
    detection_radius = 700
    attack_range     = 0          # unused — ranged enemies use preferred_range_px
    attack_cooldown  = 0
    attack_windup_ms = 0
    knockback_strength = 0
    color            = (180, 100, 220)
    xp_reward        = 30
    width            = 38
    height           = 38
    wander_radius    = 5

    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.gun              = self.gun_class()
        self.pending_bullets: list = []   # world.update() drains this each frame

        self._reposition_target: tuple[int, int] | None = None
        self._next_reposition_at: int = 0

    # =========================================================
    # PUBLIC API — override of Enemy.move()
    # =========================================================

    def move(self, player, obstacles, room, dt_ms: int):
        """Full AI update — replaces Enemy.move() for ranged enemies."""
        now = pygame.time.get_ticks()

        # Always tick gun reload
        self.gun.update_reload()

        # --- death ---
        if self.health <= 0:
            self.alive  = False
            self.state  = "dead"
            return

        if self.hit and self.state not in ("attack", "chase"):
            self.hit            = False
            self.last_seen_pos  = player.rect.center
            self.search_started = now

        # --- sense player ---
        player_center   = player.rect.center
        enemy_center    = self.rect.center
        dist2           = self._dist2(*player_center, *enemy_center)
        has_los         = False
        see_player      = False

        if dist2 <= self.detection_radius ** 2:
            has_los = self._has_los(room, *self._grid_pos(), *player._grid_pos())
            if has_los:
                see_player         = True
                self.last_seen_pos = player_center
                self.search_started = None

        self.update_knockback(obstacles)

        # --- state machine ---
        if self.state in ("idle", "walk"):
            if see_player:
                self.state               = "chase"
                self._reposition_target  = None
            else:
                self._idle(room, obstacles, dt_ms, now)

        elif self.state == "chase":
            self.wander_goal_g = None
            if not see_player:
                if self.last_seen_pos:
                    self.state          = "search"
                    self.search_started = now
                else:
                    self.state = "idle"
            else:
                self._do_chase(player, obstacles, room, dist2, has_los, dt_ms, now)

        elif self.state == "shoot":
            if not see_player or not has_los:
                # Lost sight — reposition
                self.state              = "chase"
                self._reposition_target = None
            elif self.gun.is_reloading:
                self.state = "reload"
            else:
                self._do_shoot(player_center)
                # Drift slightly if player gets too close
                if dist2 < self.min_range_px ** 2:
                    self._retreat_from(player_center, obstacles, dt_ms)

        elif self.state == "reload":
            # Back away a little while reloading — makes them feel less passive
            if see_player and dist2 < (self.preferred_range_px * 0.8) ** 2:
                self._retreat_from(player_center, obstacles, dt_ms)
            if not self.gun.is_reloading:
                self.state = "chase" if see_player else "search"

        elif self.state == "search":
            if see_player:
                self.state              = "chase"
                self._reposition_target = None
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now)
            else:
                self.state = "idle"

        elif self.state == "dead":
            return

    # =========================================================
    # DRAW — extra colour coding for new states
    # =========================================================

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        if self.state == "idle":
            color = self.color
        elif self.state == "chase":
            color = tuple(min(c + 40, 255) for c in self.color)
        elif self.state == "search":
            color = tuple(max(c - 40, 0) for c in self.color)
        elif self.state == "shoot":
            color = (255, 255, 255)   # white flash when shooting
        elif self.state == "reload":
            # Grey-ish tint + pulsing bar to telegraph "reloading"
            color = (120, 120, 140)
        elif self.state == "dead":
            color = (80, 80, 80)
        else:
            color = self.color

        pygame.draw.rect(screen, color, draw_rect)

        # Draw reload progress bar above enemy
        if self.state == "reload":
            self._draw_reload_bar(screen, draw_rect)

    # =========================================================
    # PRIVATE HELPERS
    # =========================================================

    def _do_chase(self, player, obstacles, room, dist2: float,
                  has_los: bool, dt_ms: int, now: int):
        """
        Move to a position that has LOS to the player at preferred range.
        Transitions to "shoot" once we're in a good spot.
        """
        pref2 = self.preferred_range_px ** 2
        in_range = (self.min_range_px ** 2) <= dist2 <= (self.preferred_range_px * 1.6) ** 2

        if has_los and in_range and not self.gun.is_reloading:
            # Already in a good shooting position
            self.state              = "shoot"
            self._reposition_target = None
            return

        # Find / move toward a good position
        if self._reposition_target is None or now >= self._next_reposition_at:
            self._reposition_target  = self._find_los_tile(room, player)
            self._next_reposition_at = now + self.reposition_interval

        if self._reposition_target:
            target_px = self._center_of_tile(*self._reposition_target)
            reached   = self._move_towards(target_px, obstacles, dt_ms)
            if reached:
                self._reposition_target  = None
                self._next_reposition_at = now  # search again immediately
        else:
            # No good tile found — approach cautiously
            self._move_towards(player.rect.center, obstacles, dt_ms)

    def _do_shoot(self, player_center: tuple[int, int]):
        """Fire one bullet toward the player (respects gun fire rate)."""
        direction = Vector2(
            player_center[0] - self.rect.centerx,
            player_center[1] - self.rect.centery,
        )
        if direction.length_squared() == 0:
            return
        bullets = self.gun.shoot(self.rect.center, direction)
        self.pending_bullets.extend(bullets)
        if self.gun.is_reloading:
            self.state = "reload"

    def _retreat_from(self, target_pos: tuple[int, int], obstacles, dt_ms: int):
        """Move away from target_pos (used to maintain min_range while reloading/shooting)."""
        away = Vector2(
            self.rect.centerx - target_pos[0],
            self.rect.centery - target_pos[1],
        )
        if away.length_squared() < 1e-6:
            return
        away = away.normalize()
        self._slide_move(away.x * self.speed, away.y * self.speed, dt_ms, obstacles)

    def _find_los_tile(self, room, player) -> tuple[int, int] | None:
        """
        Sample tiles at ~preferred_range from the player and return
        the closest one (to self) that has an unobstructed line-of-sight.

        Returns None if no suitable tile is found in this frame.
        """
        player_g  = player._grid_pos()
        my_g      = self._grid_pos()
        T         = constants.TILE_SIZE
        pref_g    = max(1, int(self.preferred_range_px / T))

        candidates: list[tuple[int, int]] = []

        # Sample tiles in an annulus around the player
        for _ in range(28):
            angle = random.uniform(0, math.tau)
            r     = random.uniform(pref_g * 0.55, pref_g * 1.45)
            gx    = int(player_g[0] + r * math.cos(angle))
            gy    = int(player_g[1] + r * math.sin(angle))
            if not room.is_blocked(gx, gy):
                candidates.append((gx, gy))

        # Prefer tiles closer to current position (less travel time)
        candidates.sort(
            key=lambda t: (t[0] - my_g[0]) ** 2 + (t[1] - my_g[1]) ** 2
        )

        for tile in candidates:
            if self._has_los(room, tile[0], tile[1], player_g[0], player_g[1]):
                return tile

        return None

    def _draw_reload_bar(self, screen, draw_rect: pygame.Rect):
        """Small white bar above the enemy showing reload progress."""
        bar_w  = draw_rect.width
        bar_h  = 4
        bar_x  = draw_rect.x
        bar_y  = draw_rect.y - 8

        progress = self.gun.reload_progress()
        filled_w = int(bar_w * progress)

        # Background
        pygame.draw.rect(screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h))
        # Fill
        if filled_w > 0:
            pygame.draw.rect(screen, (180, 220, 255), (bar_x, bar_y, filled_w, bar_h))