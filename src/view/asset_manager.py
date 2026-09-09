import os

import pygame


class AssetManager:

    _ASSETS_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "assets")
    )

    SPRITES_DIR = os.path.join(_ASSETS_DIR, "sprites")
    TILES_DIR   = os.path.join(_ASSETS_DIR, "tiles")

    def __init__(self):
        self._cache:   dict[str, pygame.Surface] = {}
        self._missing: set[str] = set()

    def get(self, name: str) -> pygame.Surface | None:
        """
        Load and cache an image by name.

        Maps name → assets/sprites/{name}.png
        Returns None (with one-time warning) if file is missing.
        """
        return self._load(self.SPRITES_DIR, name, f"sprite:{name}")

    def get_tile(self, name: str) -> pygame.Surface | None:
        """
        Load and cache a tile texture by name.

        Maps name → assets/tiles/{name}.png
        Returns None (with one-time warning) if file is missing.
        """
        return self._load(self.TILES_DIR, name, f"tile:{name}")

    # ------------------------------------------------------------------ #
    #  Internals
    # ------------------------------------------------------------------ #

    def _load(self, directory: str, name: str, key: str) -> pygame.Surface | None:
        if key in self._cache:
            return self._cache[key]

        if key in self._missing:
            return None

        path = os.path.join(directory, f"{name}.png")
        if not os.path.isfile(path):
            print(f"[AssetManager] Image not found: {path}")
            self._missing.add(key)
            return None

        try:
            image = pygame.image.load(path).convert_alpha()
            self._cache[key] = image
            return image
        except pygame.error as e:
            print(f"[AssetManager] Failed to load {path}: {e}")
            self._missing.add(key)
            return None


assets = AssetManager()
