import pygame

from src.core.constants import TILE_SIZE

enabled = False

HITBOX_COLOR = (255, 0, 0)

_font = None


def toggle():
    global enabled
    enabled = not enabled


def _get_font():
    global _font
    if _font is None:
        pygame.font.init()
        _font = pygame.font.SysFont("consolas", 14, bold=True)
    return _font


def draw_hitbox(screen, camera, rect):
    if enabled:
        pygame.draw.rect(screen, HITBOX_COLOR, camera.apply(rect), 2)


def draw_tile(screen, camera, grid_pos):
    if enabled:
        gx, gy = grid_pos
        tile_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, HITBOX_COLOR, camera.apply(tile_rect), 2)


def draw_line(screen, camera, start_pos, end_pos):
    if enabled:
        pygame.draw.line(
            screen, HITBOX_COLOR, camera.apply_point(start_pos), camera.apply_point(end_pos), 2
        )


def draw_circle(screen, camera, center, radius):
    if enabled:
        pygame.draw.circle(screen, HITBOX_COLOR, camera.apply_point(center), radius, 2)


def draw_label(screen, camera, world_pos, text):
    if enabled:
        surf = _get_font().render(text, True, HITBOX_COLOR)
        rect = surf.get_rect(center=camera.apply_point(world_pos))
        screen.blit(surf, rect)


def draw_overlay(screen, lines):
    if enabled:
        font = _get_font()
        surfs = [font.render(line, True, HITBOX_COLOR) for line in lines]
        y = screen.get_height() - 8 - sum(s.get_height() + 2 for s in surfs)
        for surf in surfs:
            screen.blit(surf, (8, y))
            y += surf.get_height() + 2
