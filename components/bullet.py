from __future__ import annotations

import pygame
from pygame.math import Vector2


class Bullet:
    """
    A single projectile fired by a Gun.

    All stats (damage, speed, radius, color, range) come from the
    Gun that created it — Bullet itself is just a dumb moving rect.
    """
    def __init__(
        self,
        pos,
        direction,
        speed,
        damage,
        radius,
        color,
        max_range,
    ):
        self.pos       = Vector2(pos)
        self.direction = direction.normalize()
        self.speed     = speed
        self.damage    = damage
        self.radius    = radius
        self.color     = color
        self.max_range = max_range
        self.alive     = True

        self._distance_travelled = 0.0

        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt_ms: float, obstacles: list[pygame.Rect]):
        dt       = dt_ms / 1000.0
        movement = self.direction * self.speed * dt

        self.pos                  += movement
        self._distance_travelled  += movement.length()
        self.rect.center           = (int(self.pos.x), int(self.pos.y))

        if self._distance_travelled >= self.max_range:
            self.alive = False
            return

        for obs in obstacles:
            if self.rect.colliderect(obs):
                self.alive = False
                return

    def draw(self, screen: pygame.Surface, camera):
        dr = camera.apply(self.rect)
        pygame.draw.circle(screen, self.color, dr.center, self.radius)