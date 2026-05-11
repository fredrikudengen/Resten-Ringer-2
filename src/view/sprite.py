from __future__ import annotations

import pygame

from .asset_manager import assets


class Sprite:

    def __init__(
        self,
        frames: dict[str, str | list[str]],
        base_size: tuple[int, int],
        frame_durations: dict[str, int] | None = None,
        default_duration: int = 150,
        fallback_color: tuple[int, int, int] = (255, 0, 255),
    ):
        # Normaliser: str → [str] slik at alt er en liste internt
        self._animations: dict[str, list[str]] = {
            k: ([v] if isinstance(v, str) else v)
            for k, v in frames.items()
        }
        self._frame_durations: dict[str, int] = frame_durations or {}
        self._default_duration = default_duration
        self._base_size = base_size
        self._fallback_color = fallback_color

        # Animasjons-state
        self._anim_index: dict[str, int] = {}
        self._anim_timer: dict[str, int] = {}

        # Cache — nøkkel er path, ikke state-navn
        self._scaled:  dict[str, pygame.Surface] = {}
        self._flipped: dict[str, pygame.Surface] = {}

    def draw(
        self,
        screen: pygame.Surface,
        draw_rect: pygame.Rect,
        frame: str = "idle",
        flip_x: bool = False,
        tint: tuple[int, int, int] | None = None,
        scale: float = 1.0,
        angle: float = 0.0,
        alpha: int = 255,
        y_offset: int = 0,
    ):
        path = self._current_path(frame)
        base = self._get_surface(path, flip_x) if path else None

        if base is None:
            self._draw_fallback(screen, draw_rect, alpha, y_offset)
            return

        surface = base
        owned = False

        if scale != 1.0:
            new_w = int(surface.get_width() * scale)
            new_h = int(surface.get_height() * scale)
            if new_w > 0 and new_h > 0:
                surface = pygame.transform.scale(surface, (new_w, new_h))
                owned = True

        if angle != 0.0:
            surface = pygame.transform.rotate(surface, angle)
            owned = True

        if tint is not None:
            if not owned:
                surface = surface.copy()
                owned = True
            surface.fill(tint, special_flags=pygame.BLEND_RGB_ADD)

        if alpha < 255:
            if not owned:
                surface = surface.copy()
                owned = True
            surface.set_alpha(alpha)

        blit_rect = surface.get_rect(
            center=(draw_rect.centerx, draw_rect.centery + y_offset)
        )
        screen.blit(surface, blit_rect)

    # ------------------------------------------------------------------ #
    #  Animasjonslogikk
    # ------------------------------------------------------------------ #

    def _current_path(self, state: str) -> str | None:
        frames = self._animations.get(state)
        if not frames:
            return None
        if len(frames) == 1:
            return frames[0]  # statisk frame, hopp over timer-logikk

        now = pygame.time.get_ticks()
        duration = self._frame_durations.get(state, self._default_duration)

        if state not in self._anim_timer:
            self._anim_index[state] = 0
            self._anim_timer[state] = now

        if now - self._anim_timer[state] >= duration:
            self._anim_index[state] = (self._anim_index[state] + 1) % len(frames)
            self._anim_timer[state] = now

        return frames[self._anim_index[state]]

    def current_frame_index(self, state: str) -> int:
        return self._anim_index.get(state, 0)

    # ------------------------------------------------------------------ #
    #  Surface-håndtering
    # ------------------------------------------------------------------ #

    def _get_surface(self, path: str, flip_x: bool) -> pygame.Surface | None:
        cache = self._flipped if flip_x else self._scaled

        if path in cache:
            return cache[path]

        if path not in self._scaled:
            self._load_path(path)

        base = self._scaled.get(path)
        if base is None:
            return None

        if flip_x:
            flipped = pygame.transform.flip(base, True, False)
            self._flipped[path] = flipped
            return flipped

        return base

    def _load_path(self, path: str):
        raw = assets.get(path)
        if raw is None:
            return
        scaled = pygame.transform.scale(raw, self._base_size)
        self._scaled[path] = scaled

    # ------------------------------------------------------------------ #
    #  Fallback
    # ------------------------------------------------------------------ #

    def _draw_fallback(self, screen, draw_rect, alpha, y_offset):
        fb = pygame.Surface(
            (draw_rect.width, draw_rect.height), pygame.SRCALPHA
        )
        fb.fill((*self._fallback_color, alpha))
        screen.blit(fb, (draw_rect.x, draw_rect.y + y_offset))