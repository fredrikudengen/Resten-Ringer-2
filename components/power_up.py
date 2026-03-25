import pygame
from core import constants

class BasePowerup:
    def __init__(self, x, y, size, color):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = color

    def apply(self, player):
        """Overridden by subclasses."""
        pass

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)

class SpeedPowerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.YELLOW)
        self.name = 'speed_boost'
    def apply(self, player):
        player.apply_powerup(self.name)
        
class AttackPowerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.RED)
        self.name = 'attack_boost'
    def apply(self, player):
        player.apply_powerup(self.name)

class ShieldPowerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.BLUE)
        self.name = 'shield_boost'
    def apply(self, player):
        player.apply_powerup(self.name)
