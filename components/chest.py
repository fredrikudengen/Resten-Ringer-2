import pygame
from core import constants

class Chest:
    WIDTH  = 48
    HEIGHT = 48
    COLOR  = (200, 160, 40)
    COLOR_OPENED = (80, 60, 20)

    def __init__(self, x, y):
        self.rect   = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.opened = False

    def draw(self, screen, camera):
        color = self.COLOR_OPENED if self.opened else self.COLOR
        dr = camera.apply(self.rect)
        pygame.draw.rect(screen, color, dr, border_radius=6)
        pygame.draw.rect(screen, (255, 220, 80), dr, 2, border_radius=6)