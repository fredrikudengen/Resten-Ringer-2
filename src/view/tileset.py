import pygame

from core import constants
from .asset_manager import assets


class TileSet:
    """
    Tile-teksturer skalert én gang til TILE_SIZE og cachet på navn.

    Kildebildene er 16x16, TILE_SIZE er 112 → nøyaktig 7x oppskalering.
    Bruker transform.scale (nearest), aldri smoothscale, for å bevare
    pixel-art-kantene.
    """

    def __init__(self, size: int = constants.TILE_SIZE):
        self._size = (size, size)
        self._scaled: dict[str, pygame.Surface | None] = {}

    def get(self, name: str | None) -> pygame.Surface | None:
        """Returnerer skalert tekstur, eller None hvis navnet mangler/ikke finnes."""
        if name is None:
            return None

        if name in self._scaled:
            return self._scaled[name]

        raw = assets.get_tile(name)
        surface = pygame.transform.scale(raw, self._size) if raw is not None else None
        self._scaled[name] = surface
        return surface


tileset = TileSet()
