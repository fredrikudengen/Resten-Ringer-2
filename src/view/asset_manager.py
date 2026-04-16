import os

import pygame


class AssetManager:

    SPRITES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")
    )

    def __init__(self):
        self._cache:   dict[str, pygame.Surface] = {}
        self._missing: set[str] = set()

    def get(self, name: str) -> pygame.Surface | None:
        """
        Load and cache an image by name.

        Maps name → assets/sprites/{name}.png
        Returns None (with one-time warning) if file is missing.
        """
        if name in self._cache:
            return self._cache[name]

        if name in self._missing:
            return None

        path = os.path.join(self.SPRITES_DIR, f"{name}.png")
        if not os.path.isfile(path):
            print(f"[AssetManager] Sprite not found: {path}")
            self._missing.add(name)
            return None

        try:
            image = pygame.image.load(path).convert_alpha()
            self._cache[name] = image
            return image
        except pygame.error as e:
            print(f"[AssetManager] Failed to load {path}: {e}")
            self._missing.add(name)
            return None


assets = AssetManager()