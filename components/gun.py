from __future__ import annotations

import math
import random
import pygame
from pygame.math import Vector2

from components.bullet import Bullet


class Gun:
    """
    Base class for all guns.

    Subclasses override stats and can override shoot() for
    special firing behaviour (e.g. spread shots, burst fire).

    Attributes:
        damage:       Damage per bullet
        fire_rate_ms: Minimum milliseconds between shots
        bullet_speed: Pixels per second
        bullet_radius: Visual radius of each bullet
        bullet_color:  RGB colour of each bullet
        max_range:    Max pixels a bullet travels before dying
        name:         Display name shown in HUD
    """

    damage:        float = 20.0
    fire_rate_ms:  int   = 400
    bullet_speed:  float = 600.0
    bullet_radius: int   = 5
    bullet_color:  tuple = (220, 220, 50)
    max_range:     float = 800.0
    name:          str   = "Gun"

    def __init__(self):
        self._last_shot_at: int = 0

    def can_shoot(self) -> bool:
        return pygame.time.get_ticks() - self._last_shot_at >= self.fire_rate_ms

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        """
        Fire the gun. Returns a list of Bullet objects to add to the world.
        Override in subclasses for special behaviour.
        """
        if not self.can_shoot() or direction.length_squared() == 0:
            return []

        self._last_shot_at = pygame.time.get_ticks()
        return [self._make_bullet(origin, direction)]


    # ========== Helpers ==========

    def _make_bullet(
        self,
        origin:    tuple[float, float],
        direction: Vector2,
        spread:    float = 0.0,
    ) -> Bullet:
        """
        Create a single bullet, optionally with angular spread (degrees).
        """
        if spread:
            angle = math.radians(random.uniform(-spread / 2, spread / 2))
            direction = Vector2(
                direction.x * math.cos(angle) - direction.y * math.sin(angle),
                direction.x * math.sin(angle) + direction.y * math.cos(angle),
            )

        return Bullet(
            pos       = origin,
            direction = direction,
            speed     = self.bullet_speed,
            damage    = self.damage,
            radius    = self.bullet_radius,
            color     = self.bullet_color,
            max_range = self.max_range,
        )


# ========== Concrete gun types ==========

class Pistol(Gun):
    """Balanced starting weapon. Reliable single shot."""
    name          = "Pistol"
    damage        = 20.0
    fire_rate_ms  = 350
    bullet_speed  = 650.0
    bullet_radius = 5
    bullet_color  = (220, 220, 50)
    max_range     = 800.0


class Shotgun(Gun):
    """
    Fires a spread of pellets. High damage up close,
    weak at range. Slow fire rate.
    """
    name           = "Shotgun"
    damage         = 12.0     # per pellet — 5 pellets = 60 total at point blank
    fire_rate_ms   = 750
    bullet_speed   = 500.0
    bullet_radius  = 4
    bullet_color   = (255, 140, 40)
    max_range      = 350.0    # short range intentionally
    pellets        = 5
    spread_degrees = 20.0

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        if not self.can_shoot() or direction.length_squared() == 0:
            return []
        self._last_shot_at = pygame.time.get_ticks()
        return [
            self._make_bullet(origin, direction, spread=self.spread_degrees)
            for _ in range(self.pellets)
        ]


class MachineGun(Gun):
    """Fast firing, lower damage per bullet. High spread."""
    name          = "Machine Gun"
    damage        = 10.0
    fire_rate_ms  = 100
    bullet_speed  = 700.0
    bullet_radius = 4
    bullet_color  = (100, 220, 255)
    max_range     = 750.0
    spread_degrees = 8.0

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        if not self.can_shoot() or direction.length_squared() == 0:
            return []
        self._last_shot_at = pygame.time.get_ticks()
        return [self._make_bullet(origin, direction, spread=self.spread_degrees)]


class SniperRifle(Gun):
    """
    Very high damage, very slow fire rate.
    Bullet pierces the first enemy it hits.
    """
    name          = "Sniper"
    damage        = 80.0
    fire_rate_ms  = 1200
    bullet_speed  = 1200.0
    bullet_radius = 4
    bullet_color  = (180, 80, 255)
    max_range     = 1200.0

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        if not self.can_shoot() or direction.length_squared() == 0:
            return []
        self._last_shot_at = pygame.time.get_ticks()
        bullet = self._make_bullet(origin, direction)
        bullet.piercing = True   # handled in world.update
        return [bullet]