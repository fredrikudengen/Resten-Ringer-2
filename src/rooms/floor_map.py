from __future__ import annotations

from dataclasses import dataclass, field

from .grid_room import GridRoom


DIRECTIONS: dict[str, tuple[int, int]] = {
    "N": ( 0, -1),
    "S": ( 0,  1),
    "E": ( 1,  0),
    "W": (-1,  0),
}

OPPOSITE: dict[str, str] = {"N": "S", "S": "N", "E": "W", "W": "E"}


@dataclass
class RoomNode:

    gx:          int
    gy:          int
    room_type:   str
    connections: dict[str, tuple[int, int]] = field(default_factory=dict)
    visited:     bool                       = False
    cleared:     bool                       = False
    grid_room:   GridRoom | None            = None

    @property
    def pos(self) -> tuple[int, int]:
        return (self.gx, self.gy)

    @property
    def door_sides(self) -> set[str]:
        return set(self.connections.keys())


@dataclass
class FloorMap:

    nodes:        dict[tuple[int, int], RoomNode] = field(default_factory=dict)
    start_pos:    tuple[int, int]                  = (0, 0)
    boss_pos:     tuple[int, int]                  = (0, 0)
    floor_number: int                              = 1

    def add_node(self, node: RoomNode):
        self.nodes[node.pos] = node

    def get_node(self, gx: int, gy: int) -> RoomNode | None:
        return self.nodes.get((gx, gy))

    def neighbour(self, node: RoomNode, side: str) -> RoomNode | None:
        target = node.connections.get(side)
        if target is None:
            return None
        return self.nodes.get(target)

    @property
    def room_count(self) -> int:
        return len(self.nodes)

    def connect(self, a: RoomNode, side: str, b: RoomNode):
        a.connections[side] = b.pos
        b.connections[OPPOSITE[side]] = a.pos