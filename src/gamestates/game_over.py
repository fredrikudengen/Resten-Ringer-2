from __future__ import annotations

import pygame

from .basestate import BaseState, State
from .ui_helpers import Button, draw_panel, C


class GameOverState(BaseState):

    _FADE_DELAY_MS = 400   # pause before stats fade in
    _FADE_SPEED_MS = 600   # fade-in duration

    def __init__(self, sm):
        self._sm      = sm
        self._entered = 0
        sw, sh = sm.screen.get_size()

        pygame.font.init()
        font_title     = pygame.font.SysFont('consolas', 42, bold=True)
        font_btn       = pygame.font.SysFont('consolas', 20, bold=True)
        self._font_stat = pygame.font.SysFont('consolas', 18)

        self._title = font_title.render('YOU DIED', True, C['danger'])

        btn_w, btn_h = 220, 48
        self._btn_menu = Button(
            pygame.Rect(sw // 2 - btn_w // 2, sh // 2 + 160, btn_w, btn_h),
            'BACK TO MENU', font_btn,
        )

        self._stats: list[tuple[str, str]] = []

    def on_enter(self):
        """Snapshot stats at the moment of death."""
        self._entered = pygame.time.get_ticks()
        sm = self._sm
        self._stats = [
            ('Rooms cleared',  str(sm.room_manager.rooms_cleared)),
            ('Enemies killed', str(sm.player.total_kills)),
            ('Level reached',  str(sm.player.level)),
        ]

    def handle_event(self, event: pygame.event.Event):
        if self._btn_menu.handle_event(event):
            self._sm.transition(State.MAIN_MENU)

    def draw(self, surface: pygame.Surface):
        surface.fill(C['bg'])
        sw, sh  = surface.get_size()
        elapsed = pygame.time.get_ticks() - self._entered

        surface.blit(self._title, (sw // 2 - self._title.get_width() // 2, sh // 2 - 160))

        if elapsed > self._FADE_DELAY_MS:
            alpha   = min(255, int(255 * (elapsed - self._FADE_DELAY_MS) / self._FADE_SPEED_MS))
            panel_h = len(self._stats) * 36 + 24
            panel   = pygame.Rect(sw // 2 - 160, sh // 2 - 80, 320, panel_h)
            draw_panel(surface, panel)

            for i, (label, value) in enumerate(self._stats):
                y = panel.y + 12 + i * 36

                label_surf = self._font_stat.render(label, True, C['stat_label'])
                value_surf = self._font_stat.render(value, True, C['stat_value'])
                label_surf.set_alpha(alpha)
                value_surf.set_alpha(alpha)

                surface.blit(label_surf, (panel.x + 16, y))
                surface.blit(value_surf, (panel.right - value_surf.get_width() - 16, y))

            self._btn_menu.draw(surface)