import copy

import pygame

from core import constants


class GridRoom:
    """
    A room defined by a list of strings where each character represents a tile.

    Parameters
    ----------
    lines : list[str]
        ASCII layout of the room.
    room_type : str
        Category tag ("combat", "elite", "boss", "reward", "start").
    active_doors : set[str] | None
        Which sides ("N", "S", "E", "W") should keep their door tiles.
        ``None`` means *all* potential doors stay active (legacy behaviour).
        Door tiles on sides not in this set are converted to walls.
    """

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

        # --- First pass: parse everything, treat all D tiles as doors ---
        all_door_positions: list[tuple[int, int]] = []

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                self.terrain[y][x] = constants.CHAR_TO_TILE.get(ch, constants.TILE_FLOOR)
                if ch in constants.CHAR_TO_SPAWN:
                    self.spawns[y][x] = constants.CHAR_TO_SPAWN[ch]
                    if ch == 'D':
                        all_door_positions.append((x, y))

        # --- Compute which sides have potential doors in this layout ---
        self.potential_doors: set[str] = set()
        for gx, gy in all_door_positions:
            side = self._tile_side(gx, gy)
            if side:
                self.potential_doors.add(side)

        # --- Filter: deactivate doors on unwanted sides ---
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

        # Snapshot spawns *after* filtering so reset_spawns restores
        # the filtered version, not the raw layout.
        self._original_spawns = copy.deepcopy(self.spawns)

    def _tile_side(self, gx: int, gy: int) -> str | None:
        """Return which border side a tile sits on, or None if interior."""
        if gx == 0:             return "W"
        if gx == self.cols - 1: return "E"
        if gy == 0:             return "N"
        if gy == self.rows - 1: return "S"
        return None

    def is_blocked(self, gx: int, gy: int) -> bool:
        if not (0 <= gx < self.cols and 0 <= gy < self.rows):
            return True
        return self.terrain[gy][gx] == constants.TILE_WALL

    def tile_rect(self, gx: int, gy: int) -> pygame.Rect:
        return pygame.Rect(
            gx * constants.TILE_SIZE,
            gy * constants.TILE_SIZE,
            constants.TILE_SIZE,
            constants.TILE_SIZE,
        )

    def reset_spawns(self):
        self.spawns = copy.deepcopy(self._original_spawns)