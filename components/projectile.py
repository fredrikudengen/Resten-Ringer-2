import pygame
from pygame.math import Vector2
import constants

class Projectile:
    def __init__(self, pos, direction):
            self.pos = Vector2(pos)
            self.direction = direction.normalize()
            self.speed = constants.PROJECTILE_SPEED
            self.damage = constants.PROJECTILE_DAMAGE
            self.radius = 4
            self.alive = True

            self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
            self.rect.center = self.pos

    def update(self, dt_ms, obstacles):
        dt = dt_ms / 1000.0
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos

        # kollisjon med vegg → dø
        for obs in obstacles:
            if self.rect.colliderect(obs):
                self.alive = False
                break

    def draw(self, screen, camera):
        r = camera.apply(self.rect)
        pygame.draw.circle(
            screen,
            (220, 220, 50),
            r.center,
            self.radius
        )