import random

import pytest

from rooms import floor_generator as fg
from rooms.floor_map import FloorMap, RoomNode


def test_side_between_returns_correct_direction_for_all_adjacent_deltas():
    assert fg._side_between((0, 0), (0, -1)) == "N"
    assert fg._side_between((0, 0), (0, 1)) == "S"
    assert fg._side_between((0, 0), (1, 0)) == "E"
    assert fg._side_between((0, 0), (-1, 0)) == "W"


def test_side_between_raises_for_non_adjacent_positions():
    with pytest.raises(ValueError):
        fg._side_between((0, 0), (2, 2))


def test_assign_room_types_marks_start_boss_deadend_and_combat():
    floor_map = FloorMap(start_pos=(0, 0), boss_pos=(2, 0))

    start = RoomNode(gx=0, gy=0, room_type="combat")
    middle = RoomNode(gx=1, gy=0, room_type="combat")
    boss = RoomNode(gx=2, gy=0, room_type="combat")
    deadend = RoomNode(gx=1, gy=1, room_type="combat")

    for node in (start, middle, boss, deadend):
        floor_map.add_node(node)

    start.connections["E"] = middle.pos
    middle.connections["W"] = start.pos
    middle.connections["E"] = boss.pos
    boss.connections["W"] = middle.pos
    middle.connections["S"] = deadend.pos
    deadend.connections["N"] = middle.pos

    fg._assign_room_types(floor_map)

    assert start.room_type == "start"
    assert boss.room_type == "boss"
    assert middle.room_type == "combat"  # 3 connections
    assert deadend.room_type in {name for name, _ in fg._DEADEND_WEIGHTS}


def test_generate_floor_produces_a_connected_map_with_one_start_and_boss():
    random.seed(1234)

    floor_map = fg.generate_floor(floor_number=1)

    assert fg.MIN_TOTAL_ROOMS <= floor_map.room_count <= fg.MAX_TOTAL_ROOMS

    start_nodes = [n for n in floor_map.nodes.values() if n.room_type == "start"]
    boss_nodes = [n for n in floor_map.nodes.values() if n.room_type == "boss"]
    assert len(start_nodes) == 1
    assert len(boss_nodes) == 1
    assert start_nodes[0].pos == floor_map.start_pos
    assert boss_nodes[0].pos == floor_map.boss_pos

    # Every connection must be symmetric: if A connects to B on some side,
    # B must connect back to A on the opposite side.
    for node in floor_map.nodes.values():
        for side, target_pos in node.connections.items():
            neighbour = floor_map.get_node(*target_pos)
            assert neighbour is not None
            back = neighbour.connections.get(_opposite_side(side))
            assert back == node.pos


def _opposite_side(side: str) -> str:
    return {"N": "S", "S": "N", "E": "W", "W": "E"}[side]
