import pygame
import random

class Particle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        self.timer = 500  # ms: lever i 0.5 sekunder
        self.color = color
        self.size = random.randint(2, 5)
    
    def update(self, dt):
        self.pos += self.vel
        self.timer -= dt

    def draw(self, screen, camera):
        draw_pos = camera.apply(pygame.Rect(self.pos.x, self.pos.y, self.size, self.size))
        pygame.draw.rect(screen, self.color, draw_pos)
