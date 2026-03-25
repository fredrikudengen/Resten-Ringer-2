from __future__ import annotations

import pygame

from .basestate import BaseState, State
from .ui_helpers import C

_DISPLAY_DURATION_MS = 1800   # how long the screen shows before gameplay starts
_FADE_IN_MS          = 400    # text fade-in duration
_FADE_OUT_MS         = 300    # text fade-out before transitioning

class FloorTransitionState(BaseState):
    """
    Brief interstitial screen between floors.

    On enter:
      1. Generates the next floor (fast — same frame)
      2. Shows "FLOOR N" with a short fade-in / fade-out
      3. Transitions to PlayingState after the delay
    """

    def __init__(self, sm):
        self._sm = sm
        self._entered_at = 0

        pygame.font.init()
        self._font_floor = pygame.font.SysFont("consolas", 48, bold=True)
        self._font_sub   = pygame.font.SysFont("consolas", 18)

    def on_enter(self):
        # Generate the next floor immediately
        self._sm.room_manager.advance_after_boss()

        self._entered_at = pygame.time.get_ticks()

        floor_num = self._sm.room_manager.floor_map.floor_number
        self._title_surf = self._font_floor.render(
            f"FLOOR {floor_num}", True, C["title"]
        )
        self._sub_surf = self._font_sub.render(
            "get ready", True, C["text_dim"]
        )

    def update(self, dt: int):
        elapsed = pygame.time.get_ticks() - self._entered_at
        if elapsed >= _DISPLAY_DURATION_MS:
            self._sm.transition(State.PLAYING)

    def draw(self, surface: pygame.Surface):
        surface.fill(C["bg"])
        sw, sh = surface.get_size()

        elapsed = pygame.time.get_ticks() - self._entered_at

        # Compute alpha: fade in → hold → fade out
        if elapsed < _FADE_IN_MS:
            alpha = int(255 * elapsed / _FADE_IN_MS)
        elif elapsed > _DISPLAY_DURATION_MS - _FADE_OUT_MS:
            remaining = _DISPLAY_DURATION_MS - elapsed
            alpha = int(255 * max(0, remaining) / _FADE_OUT_MS)
        else:
            alpha = 255

        title = self._title_surf.copy()
        title.set_alpha(alpha)
        surface.blit(title, (
            sw // 2 - title.get_width()  // 2,
            sh // 2 - title.get_height() // 2 - 20,
        ))

        sub = self._sub_surf.copy()
        sub.set_alpha(alpha)
        surface.blit(sub, (
            sw // 2 - sub.get_width()  // 2,
            sh // 2 + 30,
        ))