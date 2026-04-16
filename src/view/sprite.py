from __future__ import annotations

import pygame

from .asset_manager import assets


class Sprite:

    def __init__(
        self,
        frames: dict[str, str],
        base_size: tuple[int, int],
        fallback_color: tuple[int, int, int] = (255, 0, 255),
    ):
        self._frame_paths:  dict[str, str] = frames
        self._base_size:    tuple[int, int] = base_size
        self._fallback_color = fallback_color

        # Caches — populated lazily on first draw
        self._scaled:  dict[str, pygame.Surface] = {}
        self._flipped: dict[str, pygame.Surface] = {}

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

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
        """
        Draw a single frame with optional transforms.

        frame:    key into the frames dict passed at init
        flip_x:   mirror horizontally (cached — cheap)
        tint:     (r,g,b) additive colour overlay, e.g. (255,255,255) = white hit-flash
        scale:    size multiplier (1.0 = base size)
        angle:    rotation in degrees (counter-clockwise)
        alpha:    opacity 0-255
        y_offset: vertical pixel nudge (positive = down) for bob etc.
        """
        base = self._get_frame(frame, flip_x)

        if base is None:
            self._draw_fallback(screen, draw_rect, alpha, y_offset)
            return

        # ------ per-frame transforms ------ #
        # 'owned' tracks whether 'surface' is already a unique copy
        # so we avoid unnecessary .copy() calls.
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
    #  Frame loading & caching
    # ------------------------------------------------------------------ #

    def _get_frame(self, frame: str, flip_x: bool) -> pygame.Surface | None:
        """Return a cached, scaled (and optionally flipped) surface."""
        cache = self._flipped if flip_x else self._scaled

        if frame in cache:
            return cache[frame]

        # Make sure the base scaled version exists
        if frame not in self._scaled:
            self._load_frame(frame)

        base = self._scaled.get(frame)
        if base is None:
            return None

        if flip_x:
            flipped = pygame.transform.flip(base, True, False)
            self._flipped[frame] = flipped
            return flipped

        return base

    def _load_frame(self, frame: str):
        """Load from AssetManager, scale to base size, cache."""
        path = self._frame_paths.get(frame)
        if path is None:
            return

        raw = assets.get(path)
        if raw is None:
            return

        scaled = pygame.transform.scale(raw, self._base_size)
        self._scaled[frame] = scaled

    # ------------------------------------------------------------------ #
    #  Fallback
    # ------------------------------------------------------------------ #

    def _draw_fallback(self, screen, draw_rect, alpha, y_offset):
        """Draw a coloured rectangle when no sprite is available."""
        fb = pygame.Surface(
            (draw_rect.width, draw_rect.height), pygame.SRCALPHA
        )
        fb.fill((*self._fallback_color, alpha))
        screen.blit(fb, (draw_rect.x, draw_rect.y + y_offset))