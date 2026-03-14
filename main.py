import pygame
from gamestates import StateMachine

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Dungeon Crawler")
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