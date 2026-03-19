import pygame
import math
from core import constants

_C = {
    "panel":       (15,  15,  20,  200),
    "bar_bg":      (40,  40,  50,  220),

    "hp_full":     (220, 55,  55),
    "hp_low":      (220, 100, 30),
    "hp_crit":     (255, 40,  40),
    "hp_border":   (180, 40,  40),

    "xp_fill":     (80,  200, 120),
    "xp_border":   (50,  140, 80),

    "dash_ready":  (100, 180, 255),
    "dash_charge": (50,  80,  130),
    "dash_border": (60,  120, 200),

    "buff_speed":  (255, 220, 60),
    "buff_shield": (80,  160, 255),
    "buff_attack": (255, 80,  80),
    "buff_border": (200, 200, 200, 180),
    "buff_timer":  (220, 220, 220),

    "text_main":   (240, 240, 240),
    "text_dim":    (140, 140, 160),
    "text_level":  (255, 210, 60),

    "levelup":     (255, 230, 80,  180),

    # ammo
    "ammo_full":   (230, 210, 80),   # gylden – fylt patron
    "ammo_empty":  (55,  55,  65),   # mørk grå – brukt patron
    "ammo_border": (160, 140, 50),   # kant på patronikon
    "reload_fill": (100, 180, 255),  # blå reload-bar
    "reload_bg":   (30,  35,  50,  220),
    "reload_text": (180, 220, 255),
}

_BUFF_COLORS = {
    "speed_boost":  _C["buff_speed"],
    "shield_boost": _C["buff_shield"],
    "attack_boost": _C["buff_attack"],
}
_BUFF_LABELS = {
    "speed_boost":  "SPD",
    "shield_boost": "DEF",
    "attack_boost": "ATK",
}

# Maks antall patroner som vises som enkeltikoner.
# Har du flere enn dette vises de som tall i steden.
_AMMO_ICON_LIMIT = 20


def _draw_rounded_rect(surface, color, rect, radius=6):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def _draw_bar(
    surface, rect,
    value, max_value,
    fill_color, bg_color=_C["bar_bg"],
    border_color=None, border=2,
    radius=5,
    flicker=False,
):
    ratio  = max(0.0, min(1.0, value / max_value)) if max_value > 0 else 0.0
    fill_w = int(rect.width * ratio)

    _draw_rounded_rect(surface, bg_color, rect, radius)

    if fill_w > 0:
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        now   = pygame.time.get_ticks()
        color = fill_color
        if flicker and (now // 120) % 2 == 0:
            color = _C["hp_crit"]
        _draw_rounded_rect(surface, color, fill_rect, radius)

    if border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


class HUD:
    """
    Heads-Up Display for spillet.

    Tegner:
      - HP-bar med hjerteikon
      - XP-bar + level-badge
      - Ammo-widget (patronikoner eller reload-bar)
      - Dash cooldown-ring
      - Aktive buff-ikoner med tidsendrings-bar
      - Level-up flash-animasjon
    """

    PANEL_X    = 16
    PANEL_Y    = 12
    PANEL_W    = 220
    HP_BAR_H   = 18
    XP_BAR_H   = 10
    BAR_GAP    = 6
    LABEL_SIZE = 13
    LEVEL_SIZE = 15

    # Ammo
    AMMO_ROW_H      = 28   # høyde på ammo-seksjonen
    AMMO_ICON_W     = 7    # bredde på én patron
    AMMO_ICON_H     = 14   # høyde på én patron
    AMMO_ICON_GAP   = 3    # mellomrom mellom patroner
    RELOAD_BAR_H    = 8

    DASH_X_OFFSET = 16
    DASH_Y        = 16
    DASH_RADIUS   = 22

    BUFF_START_X  = 16
    BUFF_Y_OFFSET = 16
    BUFF_SIZE     = 40
    BUFF_GAP      = 8

    LEVELUP_DURATION_MS = 1800

    def __init__(self):
        pygame.font.init()
        self._font_label  = pygame.font.SysFont("consolas", self.LABEL_SIZE, bold=True)
        self._font_level  = pygame.font.SysFont("consolas", self.LEVEL_SIZE, bold=True)
        self._font_big    = pygame.font.SysFont("consolas", 26, bold=True)
        self._font_small  = pygame.font.SysFont("consolas", 11, bold=True)

        self._levelup_at  = None
        self._levelup_lvl = 1

    def notify_levelup(self, new_level: int):
        self._levelup_at  = pygame.time.get_ticks()
        self._levelup_lvl = new_level

    def draw(self, screen: pygame.Surface, player):
        sw, sh = screen.get_size()
        now    = pygame.time.get_ticks()

        self._draw_hp_xp_panel(screen, player, now)
        self._draw_dash_indicator(screen, player, now, sw)
        self._draw_buffs(screen, player, now, sh)
        self._draw_levelup_flash(screen, now, sw, sh)

    # ------------------------------------------------------------------ #
    #  HP / XP / AMMO panel
    # ------------------------------------------------------------------ #

    def _draw_hp_xp_panel(self, screen, player, now):
        x = self.PANEL_X
        y = self.PANEL_Y
        w = self.PANEL_W

        panel_h = (
            self.LABEL_SIZE + 4 +
            self.HP_BAR_H   + self.BAR_GAP +
            self.XP_BAR_H   + self.BAR_GAP +
            self.AMMO_ROW_H + 4
        )
        panel_surf = pygame.Surface((w + 16, panel_h + 12), pygame.SRCALPHA)
        panel_surf.fill(_C["panel"])
        screen.blit(panel_surf, (x - 8, y - 6))

        cy = y

        # --- HP ---
        hp_label = self._font_label.render(
            f"HP  {player.health}/{player.max_health}",
            True, _C["text_main"]
        )
        screen.blit(hp_label, (x, cy))
        cy += self.LABEL_SIZE + 4

        hp_pct = player.health / max(1, player.max_health)
        if hp_pct <= 0.15:
            hp_color, flicker = _C["hp_low"],  True
        elif hp_pct <= 0.30:
            hp_color, flicker = _C["hp_low"],  False
        else:
            hp_color, flicker = _C["hp_full"], False

        _draw_bar(
            screen, pygame.Rect(x, cy, w, self.HP_BAR_H),
            player.health, constants.PLAYER_HEALTH,
            fill_color=hp_color, border_color=_C["hp_border"], flicker=flicker,
        )
        cy += self.HP_BAR_H + self.BAR_GAP

        # --- XP ---
        xp_to_next = player.xp_to_next
        screen.blit(
            self._font_label.render(f"XP  {player.xp}/{xp_to_next}", True, _C["text_dim"]),
            (x, cy)
        )
        cy += self.LABEL_SIZE + 2

        _draw_bar(
            screen, pygame.Rect(x, cy, w, self.XP_BAR_H),
            player.xp, xp_to_next,
            fill_color=_C["xp_fill"], border_color=_C["xp_border"], radius=4,
        )
        cy += self.XP_BAR_H + self.BAR_GAP

        # --- Level badge (øverst til høyre i panelet) ---
        lv_text = self._font_level.render(f"LV {player.level}", True, _C["text_level"])
        screen.blit(lv_text, (x + w - lv_text.get_width(), self.PANEL_Y))

        # --- Ammo ---
        self._draw_ammo_row(screen, player, now, x, cy, w)

    def _draw_ammo_row(self, screen, player, now, x, cy, w):
        """
        Viser patronikoner (fylt = igjen, hul = brukt) eller
        en animert reload-bar hvis spilleren lader om.
        Uendelig ammo viser bare våpennavnet + ∞-symbol.
        """
        gun = player.gun

        # -- Gun name label --
        gun_name = getattr(gun, 'name', 'Gun')
        name_surf = self._font_small.render(gun_name.upper(), True, _C["text_dim"])
        screen.blit(name_surf, (x, cy))

        label_h = name_surf.get_height() + 3
        cy += label_h

        # -- Uendelig ammo: bare et symbol --
        if gun.ammo_infinite:
            inf_surf = self._font_label.render("∞", True, _C["ammo_full"])
            screen.blit(inf_surf, (x, cy))
            return

        max_ammo     = gun.max_ammo
        current_ammo = gun.current_ammo

        # -- Reloading: animert blå fremgangsbar --
        if gun.is_reloading:
            progress = gun.reload_progress()

            # Tekst som pulserer
            pulse      = (math.sin(now / 120) + 1) / 2   # 0 → 1
            pulse_alpha = int(160 + pulse * 95)
            rel_surf = self._font_small.render("[R]  RELOADING...", True, _C["reload_text"])
            rel_surf.set_alpha(pulse_alpha)
            screen.blit(rel_surf, (x, cy))
            cy += rel_surf.get_height() + 2

            bar_rect = pygame.Rect(x, cy, w, self.RELOAD_BAR_H)
            _draw_rounded_rect(screen, _C["bar_bg"], bar_rect, radius=4)
            if progress > 0:
                fill_w = int(w * progress)
                _draw_rounded_rect(screen, _C["reload_fill"],
                                   pygame.Rect(x, cy, fill_w, self.RELOAD_BAR_H), radius=4)
            pygame.draw.rect(screen, _C["dash_border"], bar_rect, 1, border_radius=4)
            return

        # -- Normal: patronikoner --
        # Hvis magasinet er større enn grensen, viser vi tall i steden
        if max_ammo > _AMMO_ICON_LIMIT:
            count_txt = self._font_label.render(
                f"{current_ammo} / {max_ammo}", True,
                _C["ammo_full"] if current_ammo > 0 else _C["ammo_empty"]
            )
            screen.blit(count_txt, (x, cy))
            return

        icon_w   = self.AMMO_ICON_W
        icon_h   = self.AMMO_ICON_H
        gap      = self.AMMO_ICON_GAP
        row_y    = cy + (self.AMMO_ROW_H - icon_h - name_surf.get_height() - 3) // 2

        for i in range(max_ammo):
            ix    = x + i * (icon_w + gap)
            irect = pygame.Rect(ix, row_y, icon_w, icon_h)

            if i < current_ammo:
                # Fylt patron – solid farge med lys topp
                pygame.draw.rect(screen, _C["ammo_full"],   irect, border_radius=2)
                # Liten lysrefleks øverst
                highlight = pygame.Rect(ix + 1, row_y + 1, icon_w - 2, 3)
                pygame.draw.rect(screen, (255, 240, 160), highlight, border_radius=1)
            else:
                # Tom patron – bare kontur
                pygame.draw.rect(screen, _C["ammo_empty"],  irect, border_radius=2)
                pygame.draw.rect(screen, _C["ammo_border"], irect, 1, border_radius=2)

        # Tall-fallback ved siden av ikonene hvis lite plass
        total_icon_w = max_ammo * (icon_w + gap) - gap
        if total_icon_w + 32 <= w:
            num_surf = self._font_small.render(
                f"{current_ammo}", True,
                _C["ammo_full"] if current_ammo > 0 else (180, 60, 60)
            )
            screen.blit(num_surf, (x + total_icon_w + 6, row_y + (icon_h - num_surf.get_height()) // 2))

    # ------------------------------------------------------------------ #
    #  Dash indicator
    # ------------------------------------------------------------------ #

    def _draw_dash_indicator(self, screen, player, now, screen_w):
        cx = screen_w - self.DASH_X_OFFSET - self.DASH_RADIUS
        cy = self.DASH_Y + self.DASH_RADIUS
        r  = self.DASH_RADIUS

        total_cd = constants.DASH_COOLDOWN
        elapsed  = now - (player.dash_cooldown_end - total_cd)
        ratio    = max(0.0, min(1.0, elapsed / total_cd)) if total_cd > 0 else 1.0

        pygame.draw.circle(screen, _C["dash_charge"], (cx, cy), r)

        if ratio > 0:
            segments    = max(2, int(ratio * 36))
            start_angle = -math.pi / 2
            end_angle   = start_angle + ratio * 2 * math.pi
            points      = [(cx, cy)]
            for i in range(segments + 1):
                a = start_angle + (end_angle - start_angle) * i / segments
                points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            if len(points) >= 3:
                pygame.draw.polygon(screen, _C["dash_ready"], points)

        pygame.draw.circle(screen, (20, 20, 28), (cx, cy), r - 7)
        pygame.draw.circle(screen, _C["dash_border"], (cx, cy), r, 2)

        label = self._font_label.render(
            "DASH", True,
            _C["dash_ready"] if ratio >= 1.0 else _C["text_dim"]
        )
        screen.blit(label, (cx - label.get_width() // 2, cy + r + 4))

    # ------------------------------------------------------------------ #
    #  Buff icons
    # ------------------------------------------------------------------ #

    def _draw_buffs(self, screen, player, now, screen_h):
        if not player.buff_timers:
            return

        y_base = screen_h - self.BUFF_Y_OFFSET - self.BUFF_SIZE

        for i, (name, start) in enumerate(player.buff_timers.items()):
            duration = constants.BUFF_DURATIONS.get(name, 1)
            elapsed  = now - start
            ratio    = max(0.0, 1.0 - elapsed / duration)

            bx    = self.BUFF_START_X + i * (self.BUFF_SIZE + self.BUFF_GAP)
            by    = y_base
            color = _BUFF_COLORS.get(name, (180, 180, 180))

            box_surf = pygame.Surface((self.BUFF_SIZE, self.BUFF_SIZE), pygame.SRCALPHA)
            box_surf.fill(_C["panel"])
            screen.blit(box_surf, (bx, by))
            pygame.draw.rect(screen, color, (bx, by, self.BUFF_SIZE, self.BUFF_SIZE), 2, border_radius=5)

            fill_h = int(self.BUFF_SIZE * ratio)
            if fill_h > 0:
                fill_surf = pygame.Surface((self.BUFF_SIZE - 4, fill_h), pygame.SRCALPHA)
                fill_surf.fill((*color, 60))
                screen.blit(fill_surf, (bx + 2, by + self.BUFF_SIZE - fill_h - 2))

            label = self._font_label.render(
                _BUFF_LABELS.get(name, name[:3].upper()), True, color
            )
            screen.blit(label, (
                bx + (self.BUFF_SIZE - label.get_width())  // 2,
                by + (self.BUFF_SIZE - label.get_height()) // 2,
            ))

            secs_left = max(0, (duration - elapsed) / 1000)
            screen.blit(
                self._font_label.render(f"{secs_left:.1f}s", True, _C["text_dim"]),
                (bx, by + self.BUFF_SIZE + 2)
            )

    # ------------------------------------------------------------------ #
    #  Level-up flash
    # ------------------------------------------------------------------ #

    def _draw_levelup_flash(self, screen, now, sw, sh):
        if self._levelup_at is None:
            return

        elapsed  = now - self._levelup_at
        duration = self.LEVELUP_DURATION_MS

        if elapsed > duration:
            self._levelup_at = None
            return

        alpha = int(255 * max(0.0, 1.0 - elapsed / duration))

        flash_surf = pygame.Surface((sw, 80), pygame.SRCALPHA)
        flash_surf.fill((0, 0, 0, min(160, alpha)))
        screen.blit(flash_surf, (0, sh // 2 - 40))

        text = self._font_big.render(f"LEVEL {self._levelup_lvl}!", True, _C["text_level"])
        text.set_alpha(alpha)
        screen.blit(text, (sw // 2 - text.get_width() // 2, sh // 2 - text.get_height() // 2))