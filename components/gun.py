from __future__ import annotations

import math
import random
import pygame
from pygame.math import Vector2

from components.bullet import Bullet
from core.sound_manager import sound

class Gun:

    damage:        float = 20.0
    fire_rate_ms:  int   = 400
    bullet_speed:  float = 600.0
    bullet_radius: int   = 5
    bullet_color:  tuple = (220, 220, 50)
    max_range:     float = 800.0
    name:          str   = "Gun"
    team:          str   = "player"

    max_ammo:        int = -1
    reload_time_ms:  int = 2000
    spread:          float = 0.0

    def __init__(self):
        self._last_shot_at: int        = 0
        self._reload_start: int | None = None
        self.current_ammo: int = self.max_ammo

    @property
    def is_reloading(self) -> bool:
        return self._reload_start is not None

    @property
    def ammo_infinite(self) -> bool:
        return self.max_ammo < 0

    def start_reload(self):
        if self.ammo_infinite:
            return
        if self._reload_start is None and self.current_ammo < self.max_ammo:
            self._reload_start = pygame.time.get_ticks()
            if self.team == "player":
                sound.play("reload")

    def update_reload(self):
        if self._reload_start is not None:
            if pygame.time.get_ticks() - self._reload_start >= self.reload_time_ms:
                self.current_ammo  = self.max_ammo
                self._reload_start = None

    def reload_progress(self) -> float:
        if self._reload_start is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self._reload_start
        return min(elapsed / self.reload_time_ms, 1.0)

    def can_shoot(self) -> bool:
        if self.is_reloading:
            return False
        if not self.ammo_infinite and self.current_ammo <= 0:
            return False
        return pygame.time.get_ticks() - self._last_shot_at >= self.fire_rate_ms

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        if not self.can_shoot() or direction.length_squared() == 0:
            return []

        self._last_shot_at = pygame.time.get_ticks()
        self._consume_ammo(1)
        gun_name = self.name.lower().replace(" ", "_")
        sound.play(f"{gun_name}/shoot")
        return self._fire(origin, direction)

    # ---------- Helpers ----------

    def _fire(self, origin, direction):
        return [self._make_bullet(origin, direction)]

    def _consume_ammo(self, n: int = 1):
        if self.ammo_infinite:
            return
        self.current_ammo = max(0, self.current_ammo - n)
        if self.current_ammo == 0:
            self.start_reload()

    def _make_bullet(
        self,
        origin:    tuple[float, float],
        direction: Vector2,
    ) -> Bullet:
        angle = math.radians(random.uniform(-self.spread / 2, self.spread / 2))
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
            team      = self.team,
            knockback_strength = self.knockback_strength
        )


# ========== Concrete gun types ==========

class Pistol(Gun):
    name           = "Pistol"
    damage         = 20.0
    fire_rate_ms   = 350
    bullet_speed   = 650.0
    bullet_radius  = 10
    bullet_color   = (220, 220, 50)
    spread         = 4
    max_range      = 800.0
    max_ammo       = 12
    reload_time_ms = 1400
    team = "player"
    knockback_strength = 2


class Shotgun(Gun):
    name           = "Shotgun"
    damage         = 12.0     # per skudd, 5 skudd totalt
    fire_rate_ms   = 750
    bullet_speed   = 500.0
    bullet_radius  = 7
    bullet_color   = (255, 140, 40)
    max_range      = 350.0
    pellets        = 5
    spread         = 20.0
    max_ammo       = 6
    reload_time_ms = 2000
    team = "player"
    knockback_strength = 4

    def _fire(self, origin, direction) -> list[Bullet]:
        return [self._make_bullet(origin, direction)
                for _ in range(self.pellets)]

class MachineGun(Gun):
    name           = "Machine Gun"
    damage         = 10.0
    fire_rate_ms   = 100
    bullet_speed   = 700.0
    bullet_radius  = 6
    bullet_color   = (100, 220, 255)
    max_range      = 750.0
    spread         = 8.0
    max_ammo       = 30
    reload_time_ms = 2500
    team = "player"
    knockback_strength = 1

class SniperRifle(Gun):
    name           = "Sniper"
    damage         = 30.0
    fire_rate_ms   = 1200
    bullet_speed   = 1200.0
    bullet_radius  = 8
    bullet_color   = (180, 80, 255)
    max_range      = 1200.0
    max_ammo       = 5
    reload_time_ms = 2800
    team = "player"
    knockback_strength = 3

    def _fire(self, origin, direction) -> list[Bullet]:
        b = self._make_bullet(origin, direction)
        b.piercing = True
        return [b]

class EnemyPistol(Gun):
    name           = "Enemy Pistol"
    damage         = 10.0
    fire_rate_ms   = 800
    bullet_speed   = 380.0
    bullet_radius  = 10
    bullet_color   = (200, 80, 80)
    spread         = 4
    max_range      = 700.0
    max_ammo       = 8
    reload_time_ms = 2200
    team = "enemy"
    knockback_strength = 2

class EnemyRifle(Gun):
    name           = "Enemy Rifle"
    damage         = 22.0
    fire_rate_ms   = 1400
    bullet_speed   = 1000.0
    bullet_radius  = 8
    bullet_color   = (255, 60, 60)
    max_range      = 1000.0
    max_ammo       = 5
    reload_time_ms = 3000
    team = "enemy"
    knockback_strength = 3