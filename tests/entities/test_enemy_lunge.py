import pygame

from core import constants
from entities.enemies.elite_enemies import AssassinEnemy, BruteEnemy, LungeMixin

DT = 16


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


class _OpenRoom:
    def is_blocked(self, gx, gy):
        return False


class _FakePlayer:
    def __init__(self, center):
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = center
        self.is_invincible = False
        self.health = 1000
        self.relics = []
        self.alive = True

    def _grid_pos(self):
        T = constants.TILE_SIZE
        return (self.rect.centerx // T, self.rect.centery // T)

    def apply_knockback(self, source_rect, strength):
        pass


def _make(cls, monkeypatch, now=1000):
    _set_ticks(monkeypatch, now)
    monkeypatch.setattr(cls, "stat_spread", 0)
    enemy = cls(2000, 2000)
    enemy.state = "chase"
    enemy.dir_noise_deg = 0
    return enemy


def _player_at(enemy, dx):
    return _FakePlayer((enemy.rect.centerx + dx, enemy.rect.centery))


def _run_lunge(enemy, player, monkeypatch, start=1000, frames=200):
    """Kjør move() til lungen er ferdig. Returnerer tiden da den sluttet."""
    room = _OpenRoom()
    t = start
    started = False
    for _ in range(frames):
        _set_ticks(monkeypatch, t)
        enemy.move(player, [], room, DT)
        if enemy.state == "lunge":
            started = True
        elif started:
            return t
        t += DT
    raise AssertionError("lungen ble aldri ferdig")


def test_assassin_and_brute_share_lunge_logic():
    assert issubclass(AssassinEnemy, LungeMixin)
    assert issubclass(BruteEnemy, LungeMixin)
    assert "move" not in AssassinEnemy.__dict__
    assert "_update_lunge" not in BruteEnemy.__dict__


def test_brute_has_own_lunge_tuning():
    for attr in ("_LUNGE_WINDUP", "_LUNGE_MAX_DIST", "_LUNGE_SPEED", "_LUNGE_AREA", "_LUNGE_COOLDOWN"):
        assert getattr(BruteEnemy, attr) != getattr(AssassinEnemy, attr), attr


def test_lunge_starts_with_windup_when_player_in_range(monkeypatch):
    for cls in (AssassinEnemy, BruteEnemy):
        enemy = _make(cls, monkeypatch)
        player = _player_at(enemy, 250)

        enemy.move(player, [], _OpenRoom(), DT)

        assert enemy.state == "lunge_windup", cls.__name__
        assert enemy._lunge_windup_until == 1000 + cls._LUNGE_WINDUP


def test_no_lunge_when_player_out_of_range(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    enemy.detection_radius = 10_000
    player = _player_at(enemy, 600)  # > 300 px

    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "chase"


def test_brute_uses_windup_attack_instead_of_lunge_up_close(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    player = _player_at(enemy, 70)

    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "attack"

    # Slaget på cooldown, men fortsatt for nær til å lunge
    enemy.state = "chase"
    enemy.attack_cooldown_until = 10_000
    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "chase"


def test_enemy_stands_still_during_windup(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    player = _player_at(enemy, 250)
    enemy.move(player, [], _OpenRoom(), DT)
    start = enemy.pos.copy()

    _set_ticks(monkeypatch, 1000 + BruteEnemy._LUNGE_WINDUP - 1)
    enemy.move(player, [], _OpenRoom(), DT)

    assert enemy.state == "lunge_windup"
    assert enemy.pos == start


def test_lunge_damages_player_in_path_once(monkeypatch):
    for cls in (AssassinEnemy, BruteEnemy):
        enemy = _make(cls, monkeypatch)
        player = _player_at(enemy, 250)

        _run_lunge(enemy, player, monkeypatch)

        assert player.health == 1000 - int(enemy.damage), cls.__name__


def test_lunge_stops_after_max_dist_and_starts_cooldown(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    player = _player_at(enemy, 250)
    start = enemy.pos.copy()

    end_t = _run_lunge(enemy, player, monkeypatch)

    travelled = (enemy.pos - start).length()
    assert BruteEnemy._LUNGE_MAX_DIST <= travelled <= BruteEnemy._LUNGE_MAX_DIST + BruteEnemy._LUNGE_SPEED * DT / 1000 + 1
    assert enemy.state == "chase"
    assert enemy._lunge_cooldown_until == end_t + BruteEnemy._LUNGE_COOLDOWN
    assert enemy.lunge_hit is False


def test_lunge_stops_at_wall(monkeypatch):
    enemy = _make(AssassinEnemy, monkeypatch)
    player = _player_at(enemy, 250)
    wall = pygame.Rect(enemy.rect.right + 100, enemy.rect.top - 200, 50, 400)
    room = _OpenRoom()

    enemy.move(player, [wall], room, DT)
    _set_ticks(monkeypatch, 1000 + AssassinEnemy._LUNGE_WINDUP + 1)
    enemy.move(player, [wall], room, DT)  # windup ferdig → lunge
    assert enemy.state == "lunge"

    for i in range(60):
        enemy.move(player, [wall], room, DT)
        if enemy.state != "lunge":
            break

    assert enemy.state == "chase"
    assert enemy.rect.right <= wall.left


def test_no_new_lunge_during_cooldown(monkeypatch):
    enemy = _make(AssassinEnemy, monkeypatch)
    player = _player_at(enemy, 250)
    end_t = _run_lunge(enemy, player, monkeypatch)

    player.rect.center = (enemy.rect.centerx + 250, enemy.rect.centery)
    enemy.attack_cooldown_until = 10**9
    _set_ticks(monkeypatch, end_t + 1)
    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "chase"


def test_lunge_faces_lunge_direction(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    enemy.facing_left = False
    player = _player_at(enemy, -250)

    enemy.move(player, [], _OpenRoom(), DT)
    _set_ticks(monkeypatch, 1000 + BruteEnemy._LUNGE_WINDUP + 1)
    enemy.move(player, [], _OpenRoom(), DT)

    assert enemy.state == "lunge"
    assert enemy.facing_left is True
