import pygame
import constants
import copy

CHAR_TO_TILE = {
    '.': constants.TILE_FLOOR,
    '#': constants.TILE_WALL,
}

class GridRoom:
    def __init__(self, lines):
        """
        lines: list[str], like:
        "####################",
        "#......E.......P...#",
        "#..###......###....#",
        "#..#..D.....#......#",
        "#..###......###..E.#",
        "#..................#",
        "####################",
        """
        self.rows = len(lines)
        self.cols = max(len(row) for row in lines)

        self.terrain = [[constants.TILE_FLOOR for _ in range(self.cols)] for _ in range(self.rows)]
        self.spawns  = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        self.doors   = []  # liste av dict/tuple

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                if ch in ('.', '#'):
                    self.terrain[y][x] = CHAR_TO_TILE[ch]
                elif ch == 'E':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'enemy'
                elif ch == 'S':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'speed_powerup'
                elif ch == 'A':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'attack_powerup'
                elif ch == 'H':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'shield_powerup'
                elif ch == 'D':
                    self.terrain[y][x] = constants.TILE_FLOOR
                    self.spawns[y][x] = 'door'
                    self.doors.append((x,y))

        self._original_spawns = copy.deepcopy(self.spawns)
    
    def is_blocked(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= self.cols or gy >= self.rows:
            return True
        return self.terrain[gy][gx] == constants.TILE_WALL

    def tile_rect(self, gx, gy):
        x, y = gx * constants.TILE_SIZE, gy * constants.TILE_SIZE
        return pygame.Rect(x, y, constants.TILE_SIZE, constants.TILE_SIZE)
    
    def reset_spawns(self):
        self.spawns = copy.deepcopy(self._original_spawns)


