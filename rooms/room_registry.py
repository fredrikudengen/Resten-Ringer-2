from __future__ import annotations

from dataclasses import dataclass

from .grid_room import GridRoom
from rooms import room_data as data


@dataclass
class RoomTemplate:
    """
    A raw room layout with pre-scanned metadata.

    Not a live GridRoom — call RoomRegistry.instantiate() to create one
    with specific active_doors at visit time.
    """
    lines:           list[str]
    room_type:       str
    potential_doors: set[str]   # sides that have D tiles: {"N", "S", "E", "W"}


def _scan_potential_doors(lines: list[str]) -> set[str]:
    """Scan raw ASCII lines to discover which border sides contain D tiles."""
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
    """
    Indexes every room layout file by type and door configuration.

    Usage
    -----
    registry = RoomRegistry()

    # Find all combat rooms that have doors on at least N and E:
    templates = registry.find_compatible("combat", {"N", "E"})

    # Pick one and build a live GridRoom with only those two doors active:
    room = registry.instantiate(templates[0], active_doors={"N", "E"})
    """

    def __init__(self):
        self._templates: dict[str, list[RoomTemplate]] = {}
        self._load_all()

    def find_compatible(
        self, room_type: str, required_sides: set[str]
    ) -> list[RoomTemplate]:
        """
        Return templates whose potential doors are a superset of required_sides.

        For example, required_sides={"N", "E"} matches a layout with
        potential_doors={"N", "S", "E"} but not one with only {"N", "S"}.
        """
        candidates = self._templates.get(room_type, [])
        return [t for t in candidates if required_sides <= t.potential_doors]

    def instantiate(
        self, template: RoomTemplate, active_doors: set[str]
    ) -> GridRoom:
        """Build a live GridRoom from a template, activating only the given sides."""
        return GridRoom(template.lines, template.room_type, active_doors)

    def all_templates(self, room_type: str) -> list[RoomTemplate]:
        """Return every template of a given type (unfiltered)."""
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


# ---- Legacy helper (used by current RoomManager until Step 5 rewrites it) ----

def build_rooms() -> dict[str, list[GridRoom]]:
    """Build pre-instantiated rooms with all doors active. Kept for backward compat."""
    return {
        "combat": [GridRoom(layout, room_type="combat") for layout in data.COMBAT],
        "elite":  [GridRoom(layout, room_type="elite")  for layout in data.ELITE],
        "boss":   [GridRoom(layout, room_type="boss")   for layout in data.BOSS],
        "reward": [GridRoom(layout, room_type="reward") for layout in data.REWARD],
        "start":  [GridRoom(layout, room_type="start")  for layout in data.START],
    }