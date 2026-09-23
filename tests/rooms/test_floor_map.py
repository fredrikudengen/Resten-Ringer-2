from rooms.floor_map import FloorMap, RoomNode


def test_add_node_and_get_node_round_trip():
    fm = FloorMap()
    node = RoomNode(gx=2, gy=-1, room_type="combat")
    fm.add_node(node)

    assert fm.get_node(2, -1) is node
    assert fm.get_node(0, 0) is None
    assert fm.room_count == 1


def test_connect_wires_both_sides_for_every_direction():
    for side, opposite in (("N", "S"), ("S", "N"), ("E", "W"), ("W", "E")):
        fm = FloorMap()
        a = RoomNode(gx=0, gy=0, room_type="combat")
        b = RoomNode(gx=1, gy=1, room_type="combat")
        fm.add_node(a)
        fm.add_node(b)

        fm.connect(a, side, b)

        assert a.connections[side] == b.pos
        assert b.connections[opposite] == a.pos


def test_neighbour_returns_connected_node_or_none():
    fm = FloorMap()
    a = RoomNode(gx=0, gy=0, room_type="start")
    b = RoomNode(gx=1, gy=0, room_type="combat")
    fm.add_node(a)
    fm.add_node(b)
    fm.connect(a, "E", b)

    assert fm.neighbour(a, "E") is b
    assert fm.neighbour(b, "W") is a
    assert fm.neighbour(a, "N") is None
    assert fm.neighbour(a, "S") is None


def test_room_node_pos_and_door_sides():
    node = RoomNode(gx=3, gy=4, room_type="boss")
    assert node.pos == (3, 4)
    assert node.door_sides == set()

    node.connections["N"] = (3, 3)
    node.connections["E"] = (4, 4)
    assert node.door_sides == {"N", "E"}
