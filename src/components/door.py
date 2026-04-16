import pygame
from src.core import constants


class Door:

    def __init__(self, x: int, y: int):
        self.rect     = pygame.Rect(x, y, constants.DOOR_WIDTH, constants.DOOR_HEIGHT)
        self.trigger  = self.rect.inflate(constants.TILE_SIZE / 4, constants.TILE_SIZE / 4)
        self.is_open  = False

    def draw(self, screen, camera):
        color = constants.COLOR_DOOR_OPEN if self.is_open else constants.COLOR_DOOR_CLOSED
        dr = camera.apply(self.rect)
        pygame.draw.rect(screen, color, dr)
        pygame.draw.rect(screen, constants.COLOR_DOOR_OUTLINE, dr, 2)