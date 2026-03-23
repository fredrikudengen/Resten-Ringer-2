from __future__ import annotations

import math
import random
import pygame
from pygame.math import Vector2

from components.bullet import Bullet
from core.sound_manager import sound

class Gun:
    """
    Base class for all guns.

    Subclasses override stats and can override shoot() for
    special firing behaviour (e.g. spread shots, burst fire).

    Attributes:
        damage:        Damage per bullet
        fire_rate_ms:  Minimum milliseconds between shots
        bullet_speed:  Pixels per second
        bullet_radius: Visual radius of each bullet
        bullet_color:  RGB colour of each bullet
        max_range:     Max pixels a bullet travels before dying
        name:          Display name shown in HUD
        max_ammo:      Magazine size. -1 = infinite (no ammo tracking)
        reload_time_ms: How long a full reload takes in milliseconds
    """

    damage:        float = 20.0
    fire_rate_ms:  int   = 400
    bullet_speed:  float = 600.0
    bullet_radius: int   = 5
    bullet_color:  tuple = (220, 220, 50)
    max_range:     float = 800.0
    name:          str   = "Gun"
    team:          str   = "player"

    # Ammo — set max_ammo > 0 in subclass to enable tracking
    max_ammo:        int = -1 # -1 = infinite
    reload_time_ms:  int = 2000
    spread:          float = 0.0

    def __init__(self):
        self._last_shot_at: int        = 0
        self._reload_start: int | None = None
        # Initialise current_ammo from class-level max_ammo
        self.current_ammo: int = self.max_ammo

    # ========== Ammo / reload ==========

    @property
    def is_reloading(self) -> bool:
        return self._reload_start is not None

    @property
    def ammo_infinite(self) -> bool:
        return self.max_ammo < 0

    def start_reload(self):
        """Begin reload if magazine is not already full and not already reloading."""
        if self.ammo_infinite:
            return
        if self._reload_start is None and self.current_ammo < self.max_ammo:
            self._reload_start = pygame.time.get_ticks()
            if self.team == "player":
                sound.play("reload")

    def update_reload(self):
        """
        Advance the reload timer. Must be called every frame
        (from player update or enemy move).
        """
        if self._reload_start is not None:
            if pygame.time.get_ticks() - self._reload_start >= self.reload_time_ms:
                self.current_ammo  = self.max_ammo
                self._reload_start = None

    def reload_progress(self) -> float:
        """0.0 → 1.0 fraction of reload complete. 1.0 when not reloading."""
        if self._reload_start is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self._reload_start
        return min(elapsed / self.reload_time_ms, 1.0)

    # ========== Shooting ==========

    def can_shoot(self) -> bool:
        if self.is_reloading:
            return False
        if not self.ammo_infinite and self.current_ammo <= 0:
            return False
        return pygame.time.get_ticks() - self._last_shot_at >= self.fire_rate_ms

    def shoot(self, origin: tuple[float, float], direction: Vector2) -> list[Bullet]:
        """
        Fire the gun. Returns a list of Bullet objects to add to the world.
        Override in subclasses for special behaviour.
        """
        if not self.can_shoot() or direction.length_squared() == 0:
            return []

        self._last_shot_at = pygame.time.get_ticks()
        self._consume_ammo(1)
        gun_name = self.name.lower().replace(" ", "_")
        sound.play(f"{gun_name}/shoot")
        return self._fire(origin, direction)

    # ========== Helpers ==========

    def _fire(self, origin, direction):
        """Override in subclasses to define bullet pattern."""
        return [self._make_bullet(origin, direction)]

    def _consume_ammo(self, n: int = 1):
        """Decrement ammo and auto-start reload when empty."""
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
        """
        Create a single bullet, optionally with angular spread (degrees).
        """
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
    """Balanced starting weapon. Reliable single shot."""
    name           = "Pistol"
    damage         = 20.0
    fire_rate_ms   = 350
    bullet_speed   = 650.0
    bullet_radius  = 5
    bullet_color   = (220, 220, 50)
    spread         = 4
    max_range      = 800.0
    max_ammo       = 12
    reload_time_ms = 1400
    team = "player"
    knockback_strength = 5


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
    spread         = 20.0
    max_ammo       = 6
    reload_time_ms = 2000
    team = "player"
    knockback_strength = 14

    def _fire(self, origin, direction) -> list[Bullet]:
        return [self._make_bullet(origin, direction)
                for _ in range(self.pellets)]

class MachineGun(Gun):
    """Fast firing, lower damage per bullet. High spread."""
    name           = "Machine Gun"
    damage         = 10.0
    fire_rate_ms   = 100
    bullet_speed   = 700.0
    bullet_radius  = 4
    bullet_color   = (100, 220, 255)
    max_range      = 750.0
    spread         = 8.0
    max_ammo       = 30
    reload_time_ms = 2500
    team = "player"
    knockback_strength = 3

class SniperRifle(Gun):
    """
    Very high damage, very slow fire rate.
    Bullet pierces the first enemy it hits.
    """
    name           = "Sniper"
    damage         = 30.0
    fire_rate_ms   = 1200
    bullet_speed   = 1200.0
    bullet_radius  = 4
    bullet_color   = (180, 80, 255)
    max_range      = 1200.0
    max_ammo       = 5
    reload_time_ms = 2800
    team = "player"
    knockback_strength = 8

    def _fire(self, origin, direction) -> list[Bullet]:
        b = self._make_bullet(origin, direction)
        b.piercing = True
        return [b]

# ========== Enemy-only gun variants ==========
# Weaker versions tuned for enemies — same bullet types but less damage
# and slower fire rate so ranged enemies feel fair.

class EnemyPistol(Gun):
    """Standard ranged-enemy sidearm."""
    name           = "Enemy Pistol"
    damage         = 10.0
    fire_rate_ms   = 800
    bullet_speed   = 380.0
    bullet_radius  = 4
    bullet_color   = (200, 80, 80) # reddish so player can read enemy shots
    spread         = 4
    max_range      = 700.0
    max_ammo       = 8
    reload_time_ms = 2200
    team = "enemy"
    knockback_strength = 4

class EnemyRifle(Gun):
    """High-damage slow rifle for elite ranged enemies."""
    name           = "Enemy Rifle"
    damage         = 22.0
    fire_rate_ms   = 1400
    bullet_speed   = 560.0
    bullet_radius  = 5
    bullet_color   = (255, 60, 60)
    max_range      = 1000.0
    max_ammo       = 5
    reload_time_ms = 3000
    team = "enemy"
    knockback_strength = 6