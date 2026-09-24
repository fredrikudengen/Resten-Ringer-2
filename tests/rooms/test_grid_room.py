from core import constants
from rooms.grid_room import GridRoom


# 5x5 room, doors on the E side (row 1) and the W side (row 3), plus an
# enemy spawn in the middle so reset_spawns() has something to verify.
ROOM_LINES = [
    "#####",
    "#...D",
    "#.E.#",
    "D...#",
    "#####",
]


def test_parses_terrain_and_spawns():
    room = GridRoom(ROOM_LINES, "combat")

    assert room.rows == 5 and room.cols == 5
    assert room.terrain[0][0] == constants.TILE_WALL
    assert room.terrain[2][2] == constants.TILE_FLOOR
    assert room.spawns[2][2] == "enemy"


def test_potential_doors_detected_from_edges():
    room = GridRoom(ROOM_LINES, "combat")
    assert room.potential_doors == {"E", "W"}


def test_active_doors_none_keeps_all_potential_doors_open():
    room = GridRoom(ROOM_LINES, "combat", active_doors=None)

    assert set(room.doors) == {(4, 1), (0, 3)}
    assert room.terrain[1][4] == constants.TILE_FLOOR
    assert room.terrain[3][0] == constants.TILE_FLOOR


def test_active_doors_excluding_a_side_walls_it_off():
    room = GridRoom(ROOM_LINES, "combat", active_doors={"E"})

    assert room.doors == [(4, 1)]
    assert room.terrain[1][4] == constants.TILE_FLOOR

    # The W door was not kept active, so it becomes a wall with no spawn.
    assert room.terrain[3][0] == constants.TILE_WALL
    assert room.spawns[3][0] is None


def test_is_blocked_outside_bounds_and_on_walls():
    room = GridRoom(ROOM_LINES, "combat")

    assert room.is_blocked(-1, 0) is True
    assert room.is_blocked(0, 0) is True  # wall tile
    assert room.is_blocked(2, 2) is False  # floor tile


def test_tile_side_classifies_edges_and_interior():
    room = GridRoom(ROOM_LINES, "combat")

    assert room._tile_side(0, 0) == "W"  # W checked before N for corners
    assert room._tile_side(4, 0) == "E"
    assert room._tile_side(2, 0) == "N"
    assert room._tile_side(2, 4) == "S"
    assert room._tile_side(2, 2) is None


def test_pick_variant_is_deterministic_and_respects_single_variant():
    variants = ("a", "b", "c")
    assert GridRoom._pick_variant(variants, 5, 9) == GridRoom._pick_variant(variants, 5, 9)

    single = ("only",)
    assert GridRoom._pick_variant(single, 1, 1) == "only"
    assert GridRoom._pick_variant(single, 99, -3) == "only"


def test_pick_variant_uses_multiple_variants_across_coordinates():
    variants = ("a", "b", "c")
    seen = {
        GridRoom._pick_variant(variants, gx, gy)
        for gx in range(10)
        for gy in range(10)
    }
    assert seen == set(variants)


def test_reset_spawns_restores_original_layout():
    room = GridRoom(ROOM_LINES, "combat")
    assert room.spawns[2][2] == "enemy"

    room.spawns[2][2] = None
    assert room.spawns[2][2] is None

    room.reset_spawns()
    assert room.spawns[2][2] == "enemy"
