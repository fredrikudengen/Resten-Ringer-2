"""Felles test-hjelpere: falsk klokke, åpent rom og en minimal spiller.

tests/conftest.py legger tests/ på sys.path, så testene kan gjøre `from fakes import ...`.
"""
import pygame

from core import constants


def set_ticks(monkeypatch, value: int):
    """Frys pygame.time.get_ticks() på `value` ms i stedet for å sove i testene."""
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


class OpenRoom:
    """Rom uten vegger: alt er fri sikt og fri vei."""

    def is_blocked(self, gx, gy):
        return False


class FakePlayer:
    """Det fiendene trenger av en spiller: rect, helse og knockback.

    invincible=True gjør at fiender ikke kan skade den (nyttig når testen bare ser på bevegelse).
    """

    def __init__(self, center, invincible: bool = False, health: int = 1000):
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = center
        self.is_invincible = invincible
        self.health = health
        self.relics = []
        self.alive = True
        self.hurt_invincible_until = 0

    @property
    def pos(self):
        return pygame.Vector2(self.rect.center)

    def _grid_pos(self):
        T = constants.TILE_SIZE
        return (self.rect.centerx // T, self.rect.centery // T)

    def apply_knockback(self, source_rect, strength):
        pass
