import pygame
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_src_dir = os.path.join(_project_root, "src")
for _path in (_project_root, _src_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.gamestates import StateMachine


pygame.init()

# vsync=1 is only reliably honoured by SDL in an OPENGL or SCALED display
# context — plain FULLSCREEN|DOUBLEBUF on a software surface doesn't
# guarantee it, which is why tearing (a drifting tear line, since render
# rate and monitor refresh rate aren't locked together) survived that flag
# alone. SCALED switches to SDL's accelerated renderer, where vsync=1
# actually gets enforced. Query the real desktop size first since SCALED
# needs an explicit logical size rather than the (0, 0) "auto" shorthand.
_display_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(_display_size, pygame.FULLSCREEN | pygame.SCALED, vsync=1)
pygame.display.set_caption("Resten Ringer 2")
clock = pygame.time.Clock()

sm = StateMachine(screen)

# Caps a single frame's delta so a hitch (GC pause, vsync/compositor beat,
# scheduling stall) pauses motion briefly instead of dt-scaled movement
# taking one oversized "catch-up" step and visibly teleporting the camera.
MAX_DT_MS = 50

while sm.running:
    dt = min(clock.tick(60), MAX_DT_MS)

    for event in pygame.event.get():
        sm.handle_event(event)

    sm.update(dt)
    sm.draw()
    pygame.display.flip()

pygame.quit()