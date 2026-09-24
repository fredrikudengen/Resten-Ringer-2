import pygame

from src.core.constants import TILE_SIZE

enabled = False

HITBOX_COLOR = (255, 0, 0)


def toggle():
    global enabled
    enabled = not enabled


def draw_hitbox(screen, camera, rect):
    if enabled:
        pygame.draw.rect(screen, HITBOX_COLOR, camera.apply(rect), 2)


def draw_tile(screen, camera, grid_pos):
    if enabled:
        gx, gy = grid_pos
        tile_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, HITBOX_COLOR, camera.apply(tile_rect), 2)
