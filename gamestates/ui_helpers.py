"""Reusable UI primitives shared across all states."""

from __future__ import annotations

import pygame


# Colour palette for menus and overlays (HUD has its own in constants.HUD_COLORS)
C: dict[str, tuple] = {
    'bg':           (12,  12,  18),
    'panel':        (20,  20,  30,  210),
    'title':        (255, 210, 60),
    'text':         (230, 230, 230),
    'text_dim':     (130, 130, 150),
    'btn':          (35,  35,  50),
    'btn_hover':    (60,  60,  90),
    'btn_border':   (80,  80,  120),
    'btn_selected': (80,  140, 255),
    'danger':       (220, 55,  55),
    'overlay':      (0,   0,   0,   160),
    'stat_label':   (160, 160, 180),
    'stat_value':   (255, 210, 60),
}


class Button:
    """A simple clickable button with hover highlight."""

    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font):
        self.rect    = rect
        self.label   = label
        self._font   = font
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if this button was clicked this event."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, selected: bool = False):
        color = (
            C['btn_selected'] if selected
            else C['btn_hover'] if self.hovered
            else C['btn']
        )
        pygame.draw.rect(surface, color,          self.rect, border_radius=8)
        pygame.draw.rect(surface, C['btn_border'], self.rect, 2, border_radius=8)
        text = self._font.render(self.label, True, C['text'])
        surface.blit(text, (
            self.rect.centerx - text.get_width()  // 2,
            self.rect.centery - text.get_height() // 2,
        ))


def draw_overlay(surface: pygame.Surface):
    """Semi-transparent dark overlay over the full screen."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill(C['overlay'])
    surface.blit(overlay, (0, 0))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, radius: int = 12):
    """Dark translucent panel with a subtle border."""
    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    panel.fill(C['panel'])
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, C['btn_border'], rect, 2, border_radius=radius)