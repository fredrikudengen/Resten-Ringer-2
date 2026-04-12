from __future__ import annotations

import random
import pygame

from .basestate import BaseState, State
from .ui_helpers import draw_overlay, draw_panel, C
from components.relics import ALL_RELICS
from components.gun import Pistol, Shotgun, MachineGun, SniperRifle

_ALL_GUNS = [Pistol, Shotgun, MachineGun, SniperRifle]

# TODO: change hardcode upgrade to percentage upgrade
_STAT_UPGRADES = [
    {"label": "+20 Max HP",       "color": (220, 55,  55),  "apply": lambda p: (setattr(p, "max_health", p.max_health + 20), setattr(p, "health", min(p.health + 20, p.max_health + 20)))},
    {"label": "+2 Fart",         "color": (255, 220, 60),  "apply": lambda p: setattr(p, "speed", p.speed + 2)},
    {"label": "+15% Våpen Skade",  "color": (100, 220, 255), "apply": lambda p: setattr(p.gun, "damage", round(p.gun.damage * 1.15, 1))},
    {"label": "+200 Max Ammo",    "color": (180, 255, 120), "apply": lambda p: setattr(p.gun, "max_ammo", p.gun.max_ammo + 2)},
]

_CARD_W   = 200
_CARD_H   = 300
_CARD_GAP = 40


class BossRewardState(BaseState):

    def __init__(self, sm):
        self._sm      = sm
        self._offers  = []   # populated in on_enter
        self._hovered = None

        pygame.font.init()
        self._font_type  = pygame.font.SysFont("consolas", 13)
        self._font_name  = pygame.font.SysFont("consolas", 20, bold=True)
        self._font_desc  = pygame.font.SysFont("consolas", 14)
        self._font_title = pygame.font.SysFont("consolas", 32, bold=True)

        self._title_surf = self._font_title.render("CHOOSE YOUR REWARD", True, C["title"])

    # ------------------------------------------------------------------

    def on_enter(self):
        sm     = self._sm
        player = sm.player

        other_guns = [g for g in _ALL_GUNS if not isinstance(player.gun, g)]
        gun_cls    = random.choice(other_guns)
        gun_offer  = {
            "type":  "VÅPEN",
            "label": gun_cls.name,
            "desc":  f"Bytt ut {player.gun.name}",
            "color": (220, 220, 50),
            "apply": lambda p, g=gun_cls: setattr(p, "gun", g()),
        }

        stat        = random.choice(_STAT_UPGRADES)
        stat_offer  = {
            "type":  "UPGRADE",
            "label": stat["label"],
            "desc":  "Permanent stat oppgradering",
            "color": stat["color"],
            "apply": stat["apply"],
        }

        owned       = {type(r) for r in player.relics}
        available   = [r for r in ALL_RELICS if r not in owned] or ALL_RELICS
        relic_cls   = random.choice(available)
        relic_offer = {
            "type":  "RELIC",
            "label": relic_cls.name,
            "desc":  relic_cls.description,
            "color": relic_cls.color,
            "apply": lambda p, rc=relic_cls: p.add_relic(rc),
        }

        self._offers = [gun_offer, stat_offer, relic_offer]


    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._card_at(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._card_at(event.pos)
            if idx is not None:
                self._offers[idx]["apply"](self._sm.player)
                self._sm.transition(State.FLOOR_TRANSITION)

    def draw(self, surface: pygame.Surface):
        sm = self._sm
        surface.fill((10, 10, 15))
        sm.world.draw(surface, sm.camera)
        sm.room_manager.draw(surface)
        sm.player.draw(surface, sm.camera)
        draw_overlay(surface)

        sw, sh = surface.get_size()

        surface.blit(
            self._title_surf,
            (sw // 2 - self._title_surf.get_width() // 2, sh // 2 - 220),
        )

        # Cards
        total_w = len(self._offers) * _CARD_W + (len(self._offers) - 1) * _CARD_GAP
        start_x = sw // 2 - total_w // 2
        card_y  = sh // 2 - _CARD_H // 2

        for i, offer in enumerate(self._offers):
            x        = start_x + i * (_CARD_W + _CARD_GAP)
            rect     = pygame.Rect(x, card_y, _CARD_W, _CARD_H)
            selected = (self._hovered == i)

            draw_panel(surface, rect, radius=12)
            border_color = offer["color"] if selected else C["btn_border"]
            border_w     = 3 if selected else 1
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=12)

            badge = self._font_type.render(offer["type"], True, offer["color"])
            surface.blit(badge, (rect.centerx - badge.get_width() // 2, rect.y + 16))

            swatch = pygame.Rect(rect.centerx - 30, rect.y + 40, 60, 60)
            pygame.draw.rect(surface, offer["color"], swatch, border_radius=8)

            name_surf = self._font_name.render(offer["label"], True, C["text"])
            surface.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.y + 118))

            for j, line in enumerate(self._wrap(offer["desc"], 22)):
                ls = self._font_desc.render(line, True, C["text_dim"])
                surface.blit(ls, (rect.centerx - ls.get_width() // 2, rect.y + 150 + j * 20))

    def _card_at(self, pos) -> int | None:
        sw, sh  = self._sm.screen.get_size()
        total_w = len(self._offers) * _CARD_W + (len(self._offers) - 1) * _CARD_GAP
        start_x = sw // 2 - total_w // 2
        card_y  = sh // 2 - _CARD_H // 2
        for i in range(len(self._offers)):
            x = start_x + i * (_CARD_W + _CARD_GAP)
            if pygame.Rect(x, card_y, _CARD_W, _CARD_H).collidepoint(pos):
                return i
        return None

    @staticmethod
    def _wrap(text: str, max_chars: int) -> list[str]:
        words  = text.split()
        lines, line = [], ""
        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line = (line + " " + word).strip()
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines