import pygame
from core import constants
from view.tileset import tileset


class Door:

    def __init__(self, x: int, y: int, side: str | None = None):
        self.rect     = pygame.Rect(x, y, constants.DOOR_WIDTH, constants.DOOR_HEIGHT)
        self.trigger  = self.rect.inflate(constants.TILE_SIZE / 4, constants.TILE_SIZE / 4)
        self.is_open  = False
        self.side     = side

    def draw(self, screen, camera):
        dr = camera.apply(self.rect)

        base = constants.DOOR_ART.get(self.side)
        texture = None
        if base is not None:
            suffix  = "open" if self.is_open else "closed"
            texture = tileset.get(f"{base}_{suffix}")

        if texture is not None:
            screen.blit(texture, dr)
            return

        color = constants.COLOR_DOOR_OPEN if self.is_open else constants.COLOR_DOOR_CLOSED
        pygame.draw.rect(screen, color, dr)
        pygame.draw.rect(screen, constants.COLOR_DOOR_OUTLINE, dr, 2)
