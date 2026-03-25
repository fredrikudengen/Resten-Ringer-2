import pygame
from core import constants

class BasePowerup:
    def __init__(self, x, y):
        self.size = 20
        self.rect = pygame.Rect(x, y, self.size, self.size)

    def apply(self, player):
        """Overridden by subclasses."""
        pass

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)

class HealthPowerup(BasePowerup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = constants.RED
        self.name = 'HealthPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

class SpeedPowerup(BasePowerup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = constants.YELLOW
        self.name = 'SpeedPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)
        
class AttackPowerup(BasePowerup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = constants.GREEN
        self.name = 'AttackPowerup'
    def apply(self, player):
        player.apply_powerup(self.name)

class ShieldPowerup(BasePowerup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = constants.BLUE
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
