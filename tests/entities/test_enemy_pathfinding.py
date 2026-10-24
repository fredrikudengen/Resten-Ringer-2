from core import constants
from entities.enemies.enemy import Enemy

T = constants.TILE_SIZE


class _FakeRoom:
    """Grid med valgfrie blokkerte tiles og vegg rundt (0..w-1, 0..h-1)."""

    def __init__(self, w=12, h=12, blocked=()):
        self.w, self.h = w, h
        self.blocked = set(blocked)

    def is_blocked(self, gx, gy):
        if not (0 <= gx < self.w and 0 <= gy < self.h):
            return True
        return (gx, gy) in self.blocked


class _TestEnemy(Enemy):
    name              = "test_enemy"
    speed             = 300
    health            = 40
    damage            = 5
    attack_cooldown   = 500
    knockback_strength= 6
    color             = (255, 0, 255)
    width             = 32
    height            = 32


def _enemy_at_tile(gx, gy):
    enemy = _TestEnemy(0, 0)
    enemy.pos.update(gx * T + T // 2, gy * T + T // 2)
    enemy._sync_rect_from_pos()
    return enemy


def test_astar_path_is_contiguous_and_ends_at_goal():
    room = _FakeRoom()
    enemy = _enemy_at_tile(1, 1)

    path = enemy._astar_path(room, (6, 4), max_expansions=512)

    assert path[-1] == (6, 4)
    prev = (1, 1)
    for node in path:
        assert abs(node[0] - prev[0]) + abs(node[1] - prev[1]) == 1
        prev = node
    assert len(path) == 5 + 3


def test_astar_returns_empty_when_at_goal_or_goal_blocked():
    room = _FakeRoom(blocked={(5, 5)})
    enemy = _enemy_at_tile(2, 2)

    assert enemy._astar_path(room, (2, 2), max_expansions=512) == []
    assert enemy._astar_path(room, (5, 5), max_expansions=512) == []
    assert enemy._smoothed_next_waypoint(room, (5, 5), max_expansions=512) is None


def test_smoothed_waypoint_goes_straight_to_goal_in_open_room():
    room = _FakeRoom()
    enemy = _enemy_at_tile(1, 1)

    # Rå A* går horisontalt først; smoothed går rett mot målet
    assert enemy._astar_path(room, (6, 6), max_expansions=512)[0] != (6, 6)
    assert enemy._smoothed_next_waypoint(room, (6, 6), max_expansions=512) == (6, 6)


def test_bfs_path_is_contiguous_and_respects_max_depth():
    room = _FakeRoom()
    enemy = _enemy_at_tile(2, 2)

    path = enemy._bfs_path(room, (5, 4), max_depth=6)
    assert path[-1] == (5, 4)
    assert len(path) == 3 + 2
    assert enemy._bfs_path(room, (5, 4), max_depth=4) == []


def test_micro_wander_goes_straight_in_open_room():
    room = _FakeRoom()
    enemy = _enemy_at_tile(2, 2)

    assert enemy._bfs_path(room, (5, 5), max_depth=6)[0] != (5, 5)
    assert enemy._micro_wander(room, (5, 5), max_depth=6) == (5, 5)


def test_micro_wander_routes_around_wall():
    wall = {(4, y) for y in range(0, 4)}
    room = _FakeRoom(blocked=wall)
    enemy = _enemy_at_tile(2, 1)

    waypoint = enemy._micro_wander(room, (6, 1), max_depth=12)

    assert waypoint is not None
    assert waypoint != (6, 1)
    assert enemy._has_los(room, 2, 1, *waypoint)


def test_idle_wander_does_not_end_at_intermediate_waypoint(monkeypatch):
    # Fienden står rett ved et mellompunkt (hjørnet) – turen skal fortsette
    wall = {(4, y) for y in range(0, 4)}
    room = _FakeRoom(blocked=wall)
    enemy = _enemy_at_tile(2, 1)
    enemy.wander_goal_g = (6, 1)
    enemy.wander_radius = 12

    waypoint = enemy._micro_wander(room, enemy.wander_goal_g, enemy.wander_radius)
    monkeypatch.setattr(enemy, "_move_towards", lambda *a: True)

    enemy._idle(room, [], 16, now=0)

    assert waypoint != enemy.wander_goal_g
    assert enemy.wander_goal_g == (6, 1)


def test_search_heads_straight_for_last_seen_pos_in_open_room():
    room = _FakeRoom()
    enemy = _enemy_at_tile(1, 1)
    enemy.state = "search"
    enemy.last_seen_pos = (6 * T + T // 2, 6 * T + T // 2)
    enemy.search_started = 0

    for _ in range(10):
        enemy._search([], room, 16, now=0)

    # Diagonalt mot målet, ikke bare horisontalt først
    assert enemy.velocity.x > 0
    assert enemy.velocity.y > 0
    assert enemy.state == "search"


def test_smoothed_waypoint_routes_around_wall():
    # Vertikal vegg i x=4 fra y=0..6, åpning nederst
    wall = {(4, y) for y in range(0, 7)}
    room = _FakeRoom(blocked=wall)
    enemy = _enemy_at_tile(2, 2)
    goal = (7, 2)

    waypoint = enemy._smoothed_next_waypoint(room, goal, max_expansions=512)

    assert waypoint != goal
    assert waypoint in enemy._astar_path(room, goal, max_expansions=512)
    assert enemy._has_los(room, 2, 2, *waypoint)
    # Skal ha kuttet hjørnet, ikke bare ta ett steg
    assert abs(waypoint[0] - 2) + abs(waypoint[1] - 2) > 1
