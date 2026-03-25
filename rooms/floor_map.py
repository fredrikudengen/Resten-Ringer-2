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
    """
    A single room on the floor map graph.

    Attributes
    ----------
    gx, gy : int
        Grid position on the floor map (not pixel coordinates).
    room_type : str
        "start", "combat", "elite", "reward", "boss".
    connections : dict[str, tuple[int, int]]
        Doors leading to neighbours.  Key is the side ("N", "S", "E", "W"),
        value is the (gx, gy) of the connected node.
    visited : bool
        True once the player has entered this room.
    cleared : bool
        True once all enemies in this room have been killed.
    grid_room : GridRoom | None
        The live GridRoom, instantiated when the player first visits.
        None until then.
    """
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
        """Which sides have a door (derived from connections)."""
        return set(self.connections.keys())


@dataclass
class FloorMap:
    """
    The full generated floor: a sparse grid of RoomNodes.

    Attributes
    ----------
    nodes : dict[tuple[int, int], RoomNode]
        All rooms keyed by (gx, gy).
    start_pos : tuple[int, int]
        Grid position of the start room.
    boss_pos : tuple[int, int]
        Grid position of the boss room.
    floor_number : int
        Current floor (1-based). Drives difficulty scaling.
    """
    nodes:        dict[tuple[int, int], RoomNode] = field(default_factory=dict)
    start_pos:    tuple[int, int]                  = (0, 0)
    boss_pos:     tuple[int, int]                  = (0, 0)
    floor_number: int                              = 1

    def add_node(self, node: RoomNode):
        self.nodes[node.pos] = node

    def get_node(self, gx: int, gy: int) -> RoomNode | None:
        return self.nodes.get((gx, gy))

    def neighbour(self, node: RoomNode, side: str) -> RoomNode | None:
        """Return the neighbour through a given door, or None."""
        target = node.connections.get(side)
        if target is None:
            return None
        return self.nodes.get(target)

    @property
    def room_count(self) -> int:
        return len(self.nodes)

    def connect(self, a: RoomNode, side: str, b: RoomNode):
        """Add a bidirectional door between two adjacent nodes."""
        a.connections[side] = b.pos
        b.connections[OPPOSITE[side]] = a.pos