import copy

import pygame

from src.core import constants


class GridRoom:

    def __init__(self, lines: list[str], room_type: str, active_doors: set[str] | None = None):
        self.room_type = room_type
        self.rows = len(lines)
        self.cols = max(len(row) for row in lines)

        self.terrain: list[list[int]] = [
            [constants.TILE_FLOOR for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
        self.spawns: list[list[str | None]] = [
            [None for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
        self.doors: list[tuple[int, int]] = []

        all_door_positions: list[tuple[int, int]] = []

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                self.terrain[y][x] = constants.CHAR_TO_TILE.get(ch, constants.TILE_FLOOR)
                if ch in constants.CHAR_TO_SPAWN:
                    self.spawns[y][x] = constants.CHAR_TO_SPAWN[ch]
                    if ch == 'D':
                        all_door_positions.append((x, y))

        self.potential_doors: set[str] = set()
        for gx, gy in all_door_positions:
            side = self._tile_side(gx, gy)
            if side:
                self.potential_doors.add(side)

        if active_doors is None:
            keep_sides = self.potential_doors
        else:
            keep_sides = active_doors

        for gx, gy in all_door_positions:
            side = self._tile_side(gx, gy)
            if side and side in keep_sides:
                self.doors.append((gx, gy))
            else:
                # Convert to wall
                self.terrain[gy][gx] = constants.TILE_WALL
                self.spawns[gy][gx] = None

        self._original_spawns = copy.deepcopy(self.spawns)

        # Må kjøres etter at ubrukte dører er gjort om til vegg over,
        # ellers ville autotileren sett dem som gulv.
        self.tile_art: list[list[str | None]] = self._build_tile_art()

    # ------------------------------------------------------------------ #
    #  Autotiling
    # ------------------------------------------------------------------ #

    def _build_tile_art(self) -> list[list[str | None]]:
        """Velger teksturnavn for hver vegg- og gulv-tile. None for void."""
        return [
            [self._tile_art(x, y) for x in range(self.cols)]
            for y in range(self.rows)
        ]

    def _tile_art(self, gx: int, gy: int) -> str | None:
        tile = self.terrain[gy][gx]
        if tile == constants.TILE_WALL:
            return self._wall_art(gx, gy)
        if tile == constants.TILE_FLOOR:
            return self._pick_variant(constants.TILE_ART_FLOOR, gx, gy)
        return None

    def has_wall_above(self, gx: int, gy: int) -> bool:
        """Om gulvet i (gx, gy) ligger rett under en vegg, og dermed i veggens skygge."""
        return self._is_wall(gx, gy - 1)

    def _is_floor(self, gx: int, gy: int) -> bool:
        """Gulv = innenfor rommet og verken vegg eller void. Utenfor teller ikke."""
        if not (0 <= gx < self.cols and 0 <= gy < self.rows):
            return False
        return self.terrain[gy][gx] == constants.TILE_FLOOR

    def _is_wall(self, gx: int, gy: int) -> bool:
        if not (0 <= gx < self.cols and 0 <= gy < self.rows):
            return False
        return self.terrain[gy][gx] == constants.TILE_WALL

    def _wall_art(self, gx: int, gy: int) -> str:
        """Veggen fyller alltid hele tilen, slik kollisjonen gjør.

        Med gulv rett sør synes veggens front (toppvegg). Ellers synes bare
        veggtoppen, med et kantlag mot hver side som grenser mot gulv.
        """
        if self._is_floor(gx, gy + 1):
            return self._pick_variant(constants.TILE_ART_HORIZONTAL, gx, gy)

        n = self._is_floor(gx, gy - 1)
        e = self._is_floor(gx + 1, gy)
        w = self._is_floor(gx - 1, gy)
        edges = []
        if n: edges.append("n")
        if e: edges.append("e")
        if w: edges.append("w")
        if not n and not e and self._is_floor(gx + 1, gy - 1): edges.append("ne")
        if not n and not w and self._is_floor(gx - 1, gy - 1): edges.append("nw")
        # Nabo med front (toppvegg): kanten følger fronten nedover.
        if self._is_wall(gx + 1, gy) and self._is_floor(gx + 1, gy + 1): edges.append("e_face")
        if self._is_wall(gx - 1, gy) and self._is_floor(gx - 1, gy + 1): edges.append("w_face")

        base = self._pick_variant(constants.TILE_ART_SOLID, gx, gy)
        return constants.TILE_LAYER_SEP.join([base] + [constants.TILE_ART_EDGE[k] for k in edges])

    @staticmethod
    def _pick_variant(variants: tuple[str, ...], gx: int, gy: int) -> str:
        if len(variants) == 1:
            return variants[0]
        # Deterministisk ut fra posisjon, slik at varianten er stabil
        # mellom frames og når man kommer tilbake til rommet.
        return variants[(gx * 73856093 ^ gy * 19349663) % len(variants)]

    def _tile_side(self, gx: int, gy: int) -> str | None:
        if gx == 0:             return "W"
        if gx == self.cols - 1: return "E"
        if gy == 0:             return "N"
        if gy == self.rows - 1: return "S"
        return None

    def is_blocked(self, gx: int, gy: int) -> bool:
        if not (0 <= gx < self.cols and 0 <= gy < self.rows):
            return True
        return self.terrain[gy][gx] != constants.TILE_FLOOR

    def tile_rect(self, gx: int, gy: int) -> pygame.Rect:
        return pygame.Rect(
            gx * constants.TILE_SIZE,
            gy * constants.TILE_SIZE,
            constants.TILE_SIZE,
            constants.TILE_SIZE,
        )

    def reset_spawns(self):
        self.spawns = copy.deepcopy(self._original_spawns)