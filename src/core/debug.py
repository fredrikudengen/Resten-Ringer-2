import pygame

enabled = False

HITBOX_COLOR = (255, 0, 0)


def toggle():
    global enabled
    enabled = not enabled


def draw_hitbox(screen, camera, rect):
    if enabled:
        pygame.draw.rect(screen, HITBOX_COLOR, camera.apply(rect), 2)
