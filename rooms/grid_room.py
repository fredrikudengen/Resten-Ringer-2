import copy

import pygame

from core import constants


class GridRoom:
    """
    A room defined by a list of strings where each character represents a tile.
    """

    def __init__(self, lines: list[str], room_type):
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

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                self.terrain[y][x] = constants.CHAR_TO_TILE.get(ch, constants.TILE_FLOOR)
                if ch in constants.CHAR_TO_SPAWN:
                    self.spawns[y][x] = constants.CHAR_TO_SPAWN[ch]
                    if ch == 'D':
                        self.doors.append((x, y))

        self._original_spawns = copy.deepcopy(self.spawns)

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