from __future__ import annotations

import pygame

from .basestate import BaseState, State
from .ui_helpers import Button, draw_panel, C


# Placeholder character definitions — expand when real characters exist.
CHARACTERS: list[dict] = [
    {
        'name':        'GUNNER',
        'description': 'Balanced stats. Good starting weapon.',
        'color':       (100, 180, 255),
    },
    {
        'name':        'ROGUE',
        'description': 'Fast dash. Lower health.',
        'color':       (180, 100, 255),
    },
    {
        'name':        'TANK',
        'description': 'High HP. Slower movement.',
        'color':       (255, 160, 60),
    },
]

_CARD_W = 160
_CARD_H = 220
_CARD_GAP = 24


class CharacterSelectState(BaseState):

    def __init__(self, sm):
        self._sm       = sm
        self._selected = sm.selected_character
        sw, sh = sm.screen.get_size()

        pygame.font.init()
        self._font_name = pygame.font.SysFont('consolas', 20, bold=True)
        self._font_desc = pygame.font.SysFont('consolas', 14)
        font_title      = pygame.font.SysFont('consolas', 32, bold=True)
        font_btn        = pygame.font.SysFont('consolas', 20, bold=True)

        self._title_surf = font_title.render('SELECT CHARACTER', True, C['title'])

        total_w = len(CHARACTERS) * _CARD_W + (len(CHARACTERS) - 1) * _CARD_GAP
        start_x = sw // 2 - total_w // 2
        card_y  = sh // 2 - _CARD_H // 2

        self._cards: list[pygame.Rect] = [
            pygame.Rect(start_x + i * (_CARD_W + _CARD_GAP), card_y, _CARD_W, _CARD_H)
            for i in range(len(CHARACTERS))
        ]

        btn_w, btn_h = 160, 46
        self._btn_confirm = Button(pygame.Rect(sw // 2 - btn_w - 12, sh // 2 + 150, btn_w, btn_h), 'CONFIRM', font_btn)
        self._btn_back    = Button(pygame.Rect(sw // 2 + 12,         sh // 2 + 150, btn_w, btn_h), 'BACK',    font_btn)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, card in enumerate(self._cards):
                if card.collidepoint(event.pos):
                    self._selected = i

        if self._btn_confirm.handle_event(event):
            self._sm.selected_character = self._selected
            self._sm.start_game()
        if self._btn_back.handle_event(event):
            self._sm.transition(State.MAIN_MENU)

    def draw(self, surface: pygame.Surface):
        surface.fill(C['bg'])
        sw, sh = surface.get_size()
        surface.blit(self._title_surf, (sw // 2 - self._title_surf.get_width() // 2, 60))

        for i, (card, char) in enumerate(zip(self._cards, CHARACTERS)):
            selected     = (i == self._selected)
            border_color = char['color'] if selected else C['btn_border']

            draw_panel(surface, card, radius=10)
            pygame.draw.rect(surface, border_color, card, 3 if selected else 2, border_radius=10)

            # Colour swatch
            swatch = pygame.Rect(card.x + card.w // 2 - 30, card.y + 20, 60, 60)
            pygame.draw.rect(surface, char['color'], swatch, border_radius=8)
            if selected:
                pygame.draw.rect(surface, (255, 255, 255), swatch, 2, border_radius=8)

            name_surf = self._font_name.render(char['name'], True, char['color'] if selected else C['text'])
            surface.blit(name_surf, (card.centerx - name_surf.get_width() // 2, card.y + 96))

            for j, line in enumerate(self._wrap(char['description'], 18)):
                ln_surf = self._font_desc.render(line, True, C['text_dim'])
                surface.blit(ln_surf, (card.centerx - ln_surf.get_width() // 2, card.y + 126 + j * 18))

        self._btn_confirm.draw(surface, selected=True)
        self._btn_back.draw(surface)

    @staticmethod
    def _wrap(text: str, max_chars: int) -> list[str]:
        """Naive word-wrap by character count."""
        words = text.split()
        lines, line = [], ''
        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line = (line + ' ' + word).strip()
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines