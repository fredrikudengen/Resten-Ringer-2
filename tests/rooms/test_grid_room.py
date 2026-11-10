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


# ---------- autotiling ----------

# Lukket 6x5-rom med en vegg-klump (2x1) midt i, så alle vegg-typene er med.
TILE_LINES = [
    "######",
    "#....#",
    "#.##.#",
    "#....#",
    "######",
]


def _art_in(room, gx, gy, variants):
    return room.tile_art[gy][gx] in variants


def _wall_layers(room, gx, gy):
    """(bunnlag, {kantlag}) for en vegg-tile, med kantene som nøklene i TILE_ART_EDGE."""
    base, *layers = room.tile_art[gy][gx].split(constants.TILE_LAYER_SEP)
    names = {v: k for k, v in constants.TILE_ART_EDGE.items()}
    return base, {names[layer] for layer in layers}


def test_top_wall_shows_its_front():
    room = GridRoom(TILE_LINES, "combat")
    assert _art_in(room, 2, 0, constants.TILE_ART_HORIZONTAL)


def test_other_walls_fill_the_tile_with_an_edge_towards_the_floor():
    room = GridRoom(TILE_LINES, "combat")
    expected = {
        (2, 4): {"n"},          # bunnvegg
        (0, 2): {"e"},          # vestvegg
        (5, 2): {"w"},          # østvegg
        (0, 0): {"e_face"},     # øvre venstre hjørne, ved siden av toppveggens front
        (5, 0): {"w_face"},
        (0, 4): {"ne"},         # nedre venstre hjørne
        (5, 4): {"nw"},
    }
    for (gx, gy), edges in expected.items():
        base, layers = _wall_layers(room, gx, gy)
        assert base in constants.TILE_ART_SOLID, (gx, gy)
        assert layers == edges, (gx, gy)


def test_wall_next_to_door_gets_edge_towards_the_doorway():
    # Døra er gulv i terrenget, så veggen ved siden av får kant mot døråpningen
    room = GridRoom(["#####", "#...#", "#...#", "##D##"], "combat", active_doors={"S"})
    assert _wall_layers(room, 1, 3)[1] == {"n", "e"}
    assert _wall_layers(room, 3, 3)[1] == {"n", "w"}


def test_floor_tiles_get_floor_variants_and_void_gets_none():
    room = GridRoom(["#,", "#."], "combat")
    assert room.tile_art[0][1] is None
    assert _art_in(room, 1, 1, constants.TILE_ART_FLOOR)


def test_floor_variants_are_stable_and_varied():
    lines = ["#" * 12] + ["#" + "." * 10 + "#" for _ in range(10)] + ["#" * 12]
    a, b = GridRoom(lines, "combat"), GridRoom(lines, "combat")
    floors = {a.tile_art[y][x] for y in range(1, 11) for x in range(1, 11)}
    assert a.tile_art == b.tile_art
    assert len(floors) > 1


def test_has_wall_above_marks_floor_in_wall_shadow():
    room = GridRoom(TILE_LINES, "combat")
    assert room.has_wall_above(1, 1)        # rett under toppveggen
    assert room.has_wall_above(2, 3)        # rett under vegg-klumpen
    assert not room.has_wall_above(1, 2)    # gulv over


def test_interior_pillar_is_drawn_solid_with_front_facing_south():
    lines = [
        "######",
        "#....#",
        "#.##.#",
        "#.##.#",
        "#....#",
        "######",
    ]
    room = GridRoom(lines, "combat")
    for gx in (2, 3):
        assert _wall_layers(room, gx, 2)[0] in constants.TILE_ART_SOLID   # toppen av søylen
        assert _art_in(room, gx, 3, constants.TILE_ART_HORIZONTAL)   # fronten mot sør
