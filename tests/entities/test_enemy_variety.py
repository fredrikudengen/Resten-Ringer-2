import random

import pygame

from core import constants
from entities.enemies.boss_enemies import WardenBoss
from entities.enemies.elite_enemies import ScoutEnemy
from entities.enemies.enemy import Enemy
from entities.enemies.enemy_types import ShooterEnemy, SwarmEnemy

DT = 16


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


class _TestEnemy(Enemy):
    name              = "test_enemy"
    speed             = 300
    health            = 100
    damage            = 5
    attack_cooldown   = 500
    detection_radius  = 700
    reaction_ms       = 200
    stat_spread       = 0.2
    knockback_strength= 6
    color             = (255, 0, 255)
    width             = 32
    height            = 32
    accel_time_ms     = 0
    dir_noise_deg     = 0


class _OpenRoom:
    def is_blocked(self, gx, gy):
        return False


class _FakePlayer:
    def __init__(self, center):
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = center
        self.is_invincible = True

    def _grid_pos(self):
        T = constants.TILE_SIZE
        return (self.rect.centerx // T, self.rect.centery // T)


def _make(monkeypatch, now=1000, **overrides):
    _set_ticks(monkeypatch, now)
    for k, v in overrides.items():
        monkeypatch.setattr(_TestEnemy, k, v)
    return _TestEnemy(500, 500)


# ---------- randomisering ved spawn ----------

def test_stats_stay_within_spread(monkeypatch):
    random.seed(1)
    s = _TestEnemy.stat_spread
    for _ in range(200):
        e = _make(monkeypatch)
        assert 300 * (1 - s) <= e.speed <= 300 * (1 + s)
        assert 200 * (1 - s) <= e.reaction_ms <= 200 * (1 + s)
        assert 1 - s <= e.aggression <= 1 + s


def test_aggression_shortens_cooldown_and_widens_detection(monkeypatch):
    random.seed(2)
    e = _make(monkeypatch)
    assert e.attack_cooldown == 500 / e.aggression
    assert e.detection_radius == 700 * e.aggression


def test_each_enemy_gets_its_own_values(monkeypatch):
    random.seed(3)
    speeds = {_make(monkeypatch).speed for _ in range(10)}
    assert len(speeds) == 10


def test_class_values_are_not_changed(monkeypatch):
    random.seed(4)
    _make(monkeypatch)
    assert _TestEnemy.speed == 300
    assert _TestEnemy.attack_cooldown == 500
    assert _TestEnemy.reaction_ms == 200


def test_zero_spread_keeps_class_values(monkeypatch):
    e = _make(monkeypatch, stat_spread=0)
    assert e.speed == 300
    assert e.reaction_ms == 200
    assert e.attack_cooldown == 500
    assert e.detection_radius == 700
    assert e.aggression == 1.0


def test_default_spread_comes_from_constant():
    assert Enemy.stat_spread == constants.ENEMY_STAT_SPREAD


def test_boss_is_not_randomized(monkeypatch):
    _set_ticks(monkeypatch, 1000)
    boss = WardenBoss(500, 500)
    assert boss.speed == WardenBoss.speed
    assert boss.attack_cooldown == WardenBoss.attack_cooldown


def test_scout_without_detection_radius_still_spawns(monkeypatch):
    _set_ticks(monkeypatch, 1000)
    scout = ScoutEnemy(500, 500)
    assert scout.detection_radius is None


def test_enemy_types_are_randomized(monkeypatch):
    random.seed(5)
    _set_ticks(monkeypatch, 1000)
    for cls in (SwarmEnemy, ShooterEnemy):
        speeds = {cls(500, 500).speed for _ in range(5)}
        assert len(speeds) > 1, cls.__name__


# ---------- reaksjonstid ----------

def test_idle_enemy_waits_reaction_ms_before_chasing(monkeypatch):
    e = _make(monkeypatch, stat_spread=0)
    player = _FakePlayer((e.rect.centerx + 200, e.rect.centery))
    room = _OpenRoom()

    e.move(player, [], room, DT)
    assert e.state == "idle"

    _set_ticks(monkeypatch, 1000 + 199)
    e.move(player, [], room, DT)
    assert e.state == "idle"

    _set_ticks(monkeypatch, 1000 + 200)
    e.move(player, [], room, DT)
    assert e.state == "chase"


def test_reaction_timer_resets_when_sight_is_lost(monkeypatch):
    e = _make(monkeypatch, stat_spread=0)
    room = _OpenRoom()
    near = _FakePlayer((e.rect.centerx + 200, e.rect.centery))
    far = _FakePlayer((e.rect.centerx + 5000, e.rect.centery))

    e.move(near, [], room, DT)
    _set_ticks(monkeypatch, 1000 + 150)
    e.move(far, [], room, DT)  # mister spilleren av syne

    _set_ticks(monkeypatch, 1000 + 200)
    e.move(near, [], room, DT)
    assert e.state == "idle"  # timeren startet på nytt

    _set_ticks(monkeypatch, 1000 + 400)
    e.move(near, [], room, DT)
    assert e.state == "chase"
