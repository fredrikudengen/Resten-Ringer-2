import pygame
import pytest

from entities.enemies.enemy import Enemy

DT = 16  # ms, ~60fps


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
    accel_time_ms     = 250


def _make(x=500, y=500):
    return _TestEnemy(x, y)


def test_enemy_starts_at_rest():
    enemy = _make()
    assert enemy.velocity.length() == 0


def test_one_frame_does_not_reach_full_speed():
    enemy = _make()
    enemy._steer(enemy.speed, 0, DT, [])

    expected = enemy.speed * DT / enemy.accel_time_ms
    assert enemy.velocity.x == pytest.approx(expected)
    assert enemy.velocity.x < enemy.speed


def test_reaches_full_speed_after_accel_time():
    enemy = _make()
    for _ in range(enemy.accel_time_ms // DT + 1):
        enemy._steer(enemy.speed, 0, DT, [])

    assert enemy.velocity.x == pytest.approx(enemy.speed)
    assert enemy.velocity.y == pytest.approx(0)


def test_reversing_overshoots_before_turning_back():
    enemy = _make()
    enemy.velocity.update(enemy.speed, 0)
    start_x = enemy.pos.x

    enemy._steer(-enemy.speed, 0, DT, [])

    # Fortsatt på vei mot høyre én frame etter at målet snudde
    assert enemy.velocity.x > 0
    assert enemy.pos.x > start_x


def test_turning_90_degrees_moves_in_an_arc():
    enemy = _make()
    enemy.velocity.update(enemy.speed, 0)

    enemy._steer(0, enemy.speed, DT, [])

    assert enemy.velocity.x > 0
    assert enemy.velocity.y > 0


def test_coast_brakes_when_not_steered():
    enemy = _make()
    enemy.velocity.update(enemy.speed, 0)

    enemy.coast([], DT)
    assert 0 < enemy.velocity.x < enemy.speed

    for _ in range(enemy.accel_time_ms // DT + 2):
        enemy.coast([], DT)
    assert enemy.velocity.length() == 0


def test_coast_does_nothing_after_steering_this_frame():
    enemy = _make()
    enemy._steer(enemy.speed, 0, DT, [])
    velocity = pygame.math.Vector2(enemy.velocity)

    enemy.coast([], DT)

    assert enemy.velocity == velocity
    assert enemy._steered is False


def test_wall_zeroes_blocked_axis():
    enemy = _make()
    wall = pygame.Rect(enemy.rect.right, enemy.rect.top - 100, 50, 300)
    enemy.velocity.update(enemy.speed, enemy.speed)

    enemy._steer(enemy.speed, enemy.speed, DT, [wall])

    assert enemy.velocity.x == 0
    assert enemy.velocity.y > 0


def test_zero_accel_time_means_instant():
    enemy = _make()
    enemy.accel_time_ms = 0

    enemy._steer(enemy.speed, 0, DT, [])

    assert enemy.velocity.x == enemy.speed


def test_lunge_resets_velocity():
    enemy = _make()
    enemy.velocity.update(enemy.speed, 0)

    enemy._lunge(1000, 0, DT, [])

    assert enemy.velocity.length() == 0


def test_move_towards_uses_inertia():
    enemy = _make()
    enemy._move_towards((enemy.pos.x + 1000, enemy.pos.y), [], DT)

    assert 0 < enemy.velocity.x < enemy.speed
