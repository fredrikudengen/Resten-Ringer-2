import random

import pygame
from pygame.math import Vector2

from core import constants
from entities.enemies.enemy_types import MarksmanEnemy, ShooterEnemy
from entities.enemies.ranged_enemies import RangedEnemy

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

    def _grid_pos(self):
        T = constants.TILE_SIZE
        return (self.rect.centerx // T, self.rect.centery // T)


def _make(monkeypatch, now=1000, cls=ShooterEnemy):
    _set_ticks(monkeypatch, now)
    monkeypatch.setattr(cls, "stat_spread", 0)
    enemy = cls(2000, 2000)
    enemy.dir_noise_deg = 0
    enemy.accel_time_ms = 0
    enemy.gun.spread = 0
    return enemy


def _player_right_of(enemy, dx=300):
    return (enemy.rect.centerx + dx, enemy.rect.centery)


# ---------- strafing ----------

def test_strafe_moves_sideways_relative_to_player(monkeypatch):
    enemy = _make(monkeypatch)
    start = Vector2(enemy.pos)

    enemy._strafe(_player_right_of(enemy), [], DT, now=1000)

    moved = enemy.pos - start
    assert abs(moved.y) > 0
    assert abs(moved.x) < 1e-6  # spilleren til høyre → ren sidelengs bevegelse i y
    assert abs(abs(moved.y) - enemy.speed * enemy.strafe_speed_mult * DT / 1000) < 1e-6


def test_strafe_keeps_side_within_interval_then_picks_again(monkeypatch):
    enemy = _make(monkeypatch)
    enemy._strafe(_player_right_of(enemy), [], DT, now=1000)
    switch_at = enemy._strafe_switch_at
    lo, hi = enemy.strafe_interval_ms
    assert 1000 + lo <= switch_at <= 1000 + hi

    side = enemy._strafe_dir
    enemy._strafe(_player_right_of(enemy), [], DT, now=switch_at - 1)
    assert enemy._strafe_dir == side
    assert enemy._strafe_switch_at == switch_at

    enemy._strafe(_player_right_of(enemy), [], DT, now=switch_at)
    assert enemy._strafe_switch_at > switch_at


def test_strafe_picks_both_sides_over_time(monkeypatch):
    random.seed(0)
    enemy = _make(monkeypatch)
    sides = set()
    t = 1000
    for _ in range(20):
        enemy._strafe(_player_right_of(enemy), [], DT, now=t)
        sides.add(enemy._strafe_dir)
        t = enemy._strafe_switch_at
    assert sides == {-1, 1}


def test_strafe_turns_around_at_wall(monkeypatch):
    enemy = _make(monkeypatch)
    enemy._strafe_switch_at = 10**9  # ikke bytt side tilfeldig
    enemy._strafe_dir = 1            # spiller til høyre → side = (0, 1), nedover
    wall = pygame.Rect(enemy.rect.left - 50, enemy.rect.bottom, enemy.rect.width + 100, 50)

    enemy._strafe(_player_right_of(enemy), [wall], DT, now=1000)

    assert enemy._strafe_dir == -1


def test_strafe_retreats_when_player_too_close(monkeypatch):
    enemy = _make(monkeypatch)
    start = Vector2(enemy.pos)

    enemy._strafe(_player_right_of(enemy, 50), [], DT, now=1000, retreat=True)

    moved = enemy.pos - start
    assert moved.x < 0       # bort fra spilleren
    assert abs(moved.y) > 0  # og fortsatt sidelengs


def test_shooting_enemy_strafes_and_faces_player(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.state = "shoot"
    enemy.detection_radius = 10_000
    player = _FakePlayer((enemy.rect.centerx - 300, enemy.rect.centery))  # til venstre
    start = Vector2(enemy.pos)

    enemy.move(player, [], _OpenRoom(), DT)

    assert enemy.state == "shoot"
    assert abs((enemy.pos - start).y) > 0
    assert enemy.facing_left is True


def test_zero_strafe_mult_stands_still(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.strafe_speed_mult = 0
    start = Vector2(enemy.pos)

    enemy._strafe(_player_right_of(enemy), [], DT, now=1000)

    assert enemy.pos == start


def test_marksman_strafes_slower_and_aims_better_than_shooter():
    assert MarksmanEnemy.strafe_speed_mult < ShooterEnemy.strafe_speed_mult
    assert MarksmanEnemy.aim_error_deg < ShooterEnemy.aim_error_deg


# ---------- sikteavvik ----------

def test_aim_offset_stays_within_aim_error():
    random.seed(1)
    enemy = RangedEnemy.__new__(RangedEnemy)
    enemy.aim_error_deg = 6.0
    enemy._aim_offset_deg = 0.0
    for _ in range(500):
        assert abs(enemy._next_aim_offset()) <= 6.0


def test_aim_offset_drifts_instead_of_jumping():
    random.seed(2)
    enemy = RangedEnemy.__new__(RangedEnemy)
    enemy.aim_error_deg = 6.0
    enemy._aim_offset_deg = 0.0
    prev = enemy._next_aim_offset()
    for _ in range(200):
        cur = enemy._next_aim_offset()
        assert abs(cur - prev) <= 6.0 * 0.6 + 1e-9
        prev = cur


def test_zero_aim_error_gives_no_offset():
    enemy = RangedEnemy.__new__(RangedEnemy)
    enemy.aim_error_deg = 0
    enemy._aim_offset_deg = 0.0
    assert enemy._next_aim_offset() == 0.0


def test_shot_direction_includes_aim_offset(monkeypatch):
    enemy = _make(monkeypatch)
    monkeypatch.setattr(enemy, "_next_aim_offset", lambda: 5.0)

    enemy._do_shoot(_player_right_of(enemy))

    assert len(enemy.pending_bullets) == 1
    angle = Vector2(1, 0).angle_to(enemy.pending_bullets[0].direction)
    assert abs(angle - 5.0) < 1e-6


def test_aim_offset_only_advances_when_gun_fires(monkeypatch):
    enemy = _make(monkeypatch)
    calls = []
    monkeypatch.setattr(enemy, "_next_aim_offset", lambda: calls.append(1) or 0.0)

    enemy._do_shoot(_player_right_of(enemy))
    enemy._do_shoot(_player_right_of(enemy))  # samme tick → gun på cooldown

    assert len(calls) == 1
    assert len(enemy.pending_bullets) == 1
