import pygame
import constants

class BasePowerup:
    def __init__(self, x, y, size, color):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = color

    def apply(self, player):
        """Skal overstyres i subklasser."""
        pass

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)

class Speed_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.YELLOW)
    def apply(self, player):
        player.apply_buff('speed_boost')
        
class Attack_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.RED)
    def apply(self, player):
        player.apply_buff('attack_boost')

class Shield_Powerup(BasePowerup):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, constants.BLUE)
    def apply(self, player):
        player.apply_buff('shield_boost')
