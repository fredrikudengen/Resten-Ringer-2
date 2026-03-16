from __future__ import annotations

import pygame

from .basestate import BaseState, State
from .ui_helpers import Button, draw_overlay, draw_panel, C


class PausedState(BaseState):

    def __init__(self, sm, playing_state):
        self._sm      = sm
        self._playing = playing_state
        sw, sh = sm.screen.get_size()

        pygame.font.init()
        font_title = pygame.font.SysFont('consolas', 36, bold=True)
        font_btn   = pygame.font.SysFont('consolas', 20, bold=True)

        self._title = font_title.render('PAUSED', True, C['title'])

        btn_w, btn_h = 200, 48
        cx = sw // 2 - btn_w // 2
        self._btn_resume = Button(pygame.Rect(cx, sh // 2,      btn_w, btn_h), 'RESUME',    font_btn)
        self._btn_menu   = Button(pygame.Rect(cx, sh // 2 + 64, btn_w, btn_h), 'MAIN MENU', font_btn)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._sm.transition(State.PLAYING)
        if self._btn_resume.handle_event(event):
            self._sm.transition(State.PLAYING)
        if self._btn_menu.handle_event(event):
            self._sm.transition(State.MAIN_MENU)

    def draw(self, surface: pygame.Surface):
        self._playing.draw(surface)
        draw_overlay(surface)

        sw, sh = surface.get_size()
        panel = pygame.Rect(sw // 2 - 130, sh // 2 - 60, 260, 190)
        draw_panel(surface, panel)

        surface.blit(self._title, (sw // 2 - self._title.get_width() // 2, sh // 2 - 48))
        self._btn_resume.draw(surface)
        self._btn_menu.draw(surface)