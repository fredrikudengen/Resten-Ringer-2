import pygame
from src.gamestates import StateMachine
import os
print(os.getcwd())
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Resten Ringer 2")
clock = pygame.time.Clock()

sm = StateMachine(screen)

while sm.running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        sm.handle_event(event)

    sm.update(dt)
    sm.draw()
    pygame.display.flip()

pygame.quit()