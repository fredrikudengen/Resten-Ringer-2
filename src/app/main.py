import pygame
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_src_dir = os.path.join(_project_root, "src")
for _path in (_project_root, _src_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.gamestates import StateMachine
from src.view.sound_manager import sound


pygame.init()

_display_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(_display_size, pygame.FULLSCREEN | pygame.SCALED, vsync=1)
pygame.display.set_caption("Resten Ringer 2")
clock = pygame.time.Clock()
sm = StateMachine(screen)
MAX_DT_MS = 50

while sm.running:
    dt = min(clock.tick(60), MAX_DT_MS)

    for event in pygame.event.get():
        sm.handle_event(event)

    sm.update(dt)
    sound.update()
    sm.draw()
    pygame.display.flip()

pygame.quit()