import pygame

class Camera:
    def __init__(self, screen_width, screen_height):
        self.sw, self.sh = screen_width, screen_height
        self.offset = pygame.Vector2(0, 0)

    def update(self, target_rect):
        self.offset.x = target_rect.centerx - self.sw // 2
        self.offset.y = target_rect.centery - self.sh // 2

    def apply(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)

    def screen_to_world(self, x, y):
        return pygame.Vector2(
            x + self.offset.x,
            y + self.offset.y
        )
