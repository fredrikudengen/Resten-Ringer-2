from __future__ import annotations

import pygame
from enum import Enum, auto


class State(Enum):
    MAIN_MENU        = auto()
    CHARACTER_SELECT = auto()
    PLAYING          = auto()
    PAUSED           = auto()
    GAME_OVER        = auto()
    BOSS_REWARD      = auto()


class BaseState:
    """Every state implements these three methods."""

    def handle_event(self, event: pygame.event.Event): pass
    def update(self, dt: int): pass
    def draw(self, surface: pygame.Surface): pass
    def on_enter(self): pass