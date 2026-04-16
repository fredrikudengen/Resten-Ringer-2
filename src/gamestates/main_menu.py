from __future__ import annotations

import math
import pygame

from .basestate import BaseState, State
from .ui_helpers import Button, C


class MainMenuState(BaseState):

    def __init__(self, sm):
        self._sm = sm
        sw, sh   = sm.screen.get_size()

        pygame.font.init()
        font_title = pygame.font.SysFont('consolas', 52, bold=True)
        font_btn   = pygame.font.SysFont('consolas', 22, bold=True)
        font_sub   = pygame.font.SysFont('consolas', 16)

        self._title    = font_title.render('Resten Ringer 2', True, C['title'])
        self._subtitle = font_sub.render('Klar for en runde til?', True, C['text_dim'])

        btn_w, btn_h = 240, 52
        cx = sw // 2 - btn_w // 2

        self._btn_play = Button(pygame.Rect(cx, sh // 2 - 20,  btn_w, btn_h), 'SPILL', font_btn)
        self._btn_char = Button(pygame.Rect(cx, sh // 2 + 48,  btn_w, btn_h), 'VELG KARAKTER', font_btn)
        self._btn_quit = Button(pygame.Rect(cx, sh // 2 + 116, btn_w, btn_h), 'AVSLUTT', font_btn)

        self._t = 0.0

    def handle_event(self, event: pygame.event.Event):
        if self._btn_play.handle_event(event):
            self._sm.start_game()
        if self._btn_char.handle_event(event):
            self._sm.transition(State.CHARACTER_SELECT)
        if self._btn_quit.handle_event(event):
            self._sm.running = False

    def update(self, dt: int):
        self._t += dt * 0.001

    def draw(self, surface: pygame.Surface):
        surface.fill(C['bg'])
        sw, sh = surface.get_size()

        # Pulsing title alpha
        title_copy = self._title.copy()
        title_copy.set_alpha(int(220 + 35 * math.sin(self._t * 1.5)))

        surface.blit(title_copy,    (sw // 2 - self._title.get_width()    // 2, sh // 2 - 140))
        surface.blit(self._subtitle,(sw // 2 - self._subtitle.get_width() // 2, sh // 2 - 88))

        self._btn_play.draw(surface)
        self._btn_char.draw(surface)
        self._btn_quit.draw(surface)