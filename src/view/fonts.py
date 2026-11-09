from functools import lru_cache

import pygame

DEFAULT_FONT = "consolas"


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False, name: str = DEFAULT_FONT) -> pygame.font.Font:
    """Hent en font fra cachen (lages første gang).

    pygame.font.SysFont søker gjennom systemfontene hver gang, så den er treg å kalle ofte.
    Bruk denne overalt, så holder det å bytte DEFAULT_FONT for å endre fonten i hele spillet.
    """
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.SysFont(name, size, bold=bold)
