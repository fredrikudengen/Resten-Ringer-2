import pygame
from src.gamestates import StateMachine
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_src_dir = os.path.join(_project_root, "src")
for _path in (_project_root, _src_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)

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