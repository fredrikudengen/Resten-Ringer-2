import pygame
from core import constants
from view.sprite import Sprite
from view.tileset import tileset

ICON_SIZE = 64


class BasePowerup:
    icon_frame = None
    color = constants.WHITE

    def __init__(self, x, y):
        self.size = constants.TILE_SIZE
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.sprite = Sprite(
            frames={"idle": self.icon_frame} if self.icon_frame else {},
            base_size=(ICON_SIZE, ICON_SIZE),
            fallback_color=self.color
        )

    def apply(self, player):
        pass

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        floor_texture = tileset.get("floor_1")
        if floor_texture is not None:
            screen.blit(floor_texture, draw_rect)
        else:
            pygame.draw.rect(screen, constants.TILE_FLOOR_COLOR, draw_rect)

        icon_rect = pygame.Rect(0, 0, ICON_SIZE, ICON_SIZE)
        icon_rect.center = draw_rect.center
        self.sprite.draw(screen, icon_rect)

class HealthPowerup(BasePowerup):
    icon_frame = "ui/health"
    color = constants.RED

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = 'HealthPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

class SpeedPowerup(BasePowerup):
    icon_frame = "ui/speed"
    color = constants.YELLOW

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = 'SpeedPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

class AttackPowerup(BasePowerup):
    icon_frame = "ui/attack"
    color = constants.GREEN

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = 'AttackPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

class ShieldPowerup(BasePowerup):
    icon_frame = "ui/shield"
    color = constants.BLUE

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = 'ShieldPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

POWERUP_TYPES = {
    "Powerup": BasePowerup,
    "ShieldPowerup": ShieldPowerup,
    "SpeedPowerup": SpeedPowerup,
    "HealthPowerup": HealthPowerup,
    "AttackPowerup": AttackPowerup,
}
