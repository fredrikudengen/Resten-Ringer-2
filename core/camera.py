import random

import pygame

class Camera:
    def __init__(self, screen_width, screen_height):
        self.sw, self.sh = screen_width, screen_height
        self.offset = pygame.Vector2(0, 0)
        self._shake_intensity = 0
        self._shake_until = 0
        self._shake_offset = pygame.Vector2(0, 0)

    def update(self, target_rect):
        if pygame.time.get_ticks() < self._shake_until:
            self._shake_offset.x = random.randint(-self._shake_intensity, self._shake_intensity)
            self._shake_offset.y = random.randint(-self._shake_intensity, self._shake_intensity)
        else:
            self._shake_offset.x = 0
            self._shake_offset.y = 0
        self.offset.x = target_rect.centerx - self.sw // 2
        self.offset.y = target_rect.centery - self.sh // 2

    def apply(self, rect):
        return rect.move(-(self.offset + self._shake_offset))

    def screen_to_world(self, x, y):
        return pygame.Vector2(
            x + self.offset.x,
            y + self.offset.y
        )

    def shake(self, intensity, duration_ms):
        self._shake_intensity = intensity
        self._shake_until = pygame.time.get_ticks() + duration_ms


