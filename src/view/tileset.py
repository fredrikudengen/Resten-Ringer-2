import pygame

from src.core import constants
from src.view.asset_manager import assets


class TileSet:
    """
    Tile-teksturer skalert én gang til TILE_SIZE og cachet på navn.

    Kildebildene er 32x32, TILE_SIZE er 96 → nøyaktig 3x oppskalering,
    samme pikselskala som spillerspritene. Navn med "+" (TILE_LAYER_SEP)
    settes sammen av flere lag, f.eks. "wall_solid_1+wall_edge_e".
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

        if constants.TILE_LAYER_SEP in name:
            surface = self._compose(name.split(constants.TILE_LAYER_SEP))
        else:
            raw = assets.get_tile(name)
            surface = pygame.transform.scale(raw, self._size) if raw is not None else None
        self._scaled[name] = surface
        return surface

    def _compose(self, layers: list[str]) -> pygame.Surface | None:
        """Legger lagene oppå hverandre (f.eks. veggtopp + kantlag). None hvis bunnlaget mangler."""
        base = self.get(layers[0])
        if base is None:
            return None
        surface = base.copy()
        for layer in layers[1:]:
            overlay = self.get(layer)
            if overlay is not None:
                surface.blit(overlay, (0, 0))
        return surface


tileset = TileSet()
