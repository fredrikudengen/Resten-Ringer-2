from rooms.room_registry import RoomRegistry, RoomTemplate, _scan_potential_doors


def test_scan_potential_doors_detects_each_edge():
    lines = [
        "..D.",
        "...D",
        "D...",
        "....",
    ]
    assert _scan_potential_doors(lines) == {"N", "E", "W"}


def test_scan_potential_doors_returns_empty_set_when_no_doors():
    lines = [
        "###",
        "#.#",
        "###",
    ]
    assert _scan_potential_doors(lines) == set()


def test_find_compatible_returns_only_templates_covering_required_sides():
    registry = RoomRegistry.__new__(RoomRegistry)
    registry._templates = {
        "combat": [
            RoomTemplate(lines=["ns"], room_type="combat", potential_doors={"N", "S"}),
            RoomTemplate(lines=["nsew"], room_type="combat", potential_doors={"N", "S", "E", "W"}),
            RoomTemplate(lines=["e"], room_type="combat", potential_doors={"E"}),
        ],
        "boss": [
            RoomTemplate(lines=["boss_ns"], room_type="boss", potential_doors={"N", "S"}),
        ],
    }

    result = registry.find_compatible("combat", {"N", "S"})

    assert {t.lines[0] for t in result} == {"ns", "nsew"}


def test_find_compatible_returns_empty_list_for_unknown_room_type():
    registry = RoomRegistry.__new__(RoomRegistry)
    registry._templates = {}

    assert registry.find_compatible("combat", {"N"}) == []
