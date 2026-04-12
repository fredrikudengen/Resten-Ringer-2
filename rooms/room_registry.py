from dataclasses import dataclass

from .grid_room import GridRoom
from rooms import room_data as data


@dataclass
class RoomTemplate:

    lines:           list[str]
    room_type:       str
    potential_doors: set[str]   # sides that have D tiles: {"N", "S", "E", "W"}


def _scan_potential_doors(lines: list[str]) -> set[str]:
    rows = len(lines)
    cols = max(len(row) for row in lines)
    sides: set[str] = set()
    for y, row in enumerate(lines):
        for x, ch in enumerate(row):
            if ch == 'D':
                if y == 0:          sides.add("N")
                if y == rows - 1:   sides.add("S")
                if x == 0:          sides.add("W")
                if x == cols - 1:   sides.add("E")
    return sides


class RoomRegistry:

    def __init__(self):
        self._templates: dict[str, list[RoomTemplate]] = {}
        self._load_all()

    def find_compatible(
        self, room_type: str, required_sides: set[str]
    ) -> list[RoomTemplate]:

        candidates = self._templates.get(room_type, [])
        return [t for t in candidates if required_sides <= t.potential_doors]

    def instantiate(
        self, template: RoomTemplate, active_doors: set[str]
    ) -> GridRoom:
        return GridRoom(template.lines, template.room_type, active_doors)

    def all_templates(self, room_type: str) -> list[RoomTemplate]:
        return list(self._templates.get(room_type, []))

    def _load_all(self):
        categories = [
            ("combat", data.COMBAT),
            ("elite",  data.ELITE),
            ("boss",   data.BOSS),
            ("reward", data.REWARD),
            ("start",  data.START),
        ]
        for room_type, layouts in categories:
            templates: list[RoomTemplate] = []
            for lines in layouts:
                potential = _scan_potential_doors(lines)
                templates.append(RoomTemplate(lines, room_type, potential))
            self._templates[room_type] = templates