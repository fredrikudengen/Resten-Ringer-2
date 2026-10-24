import math

import pytest

from core import constants
from entities.enemies.enemy import Enemy

T = constants.TILE_SIZE
DT = 16
FAR = 10 * T  # langt nok unna til at støyen ikke er tonet ned


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
    dir_noise_deg     = 15
    dir_noise_hz      = 0.35


def _make(phase=(0.3, 1.7)):
    enemy = _TestEnemy(500, 500)
    enemy._noise_phase = phase
    return enemy


def _sample(enemy, frames, dist=FAR):
    return [enemy._direction_noise_deg(DT, dist) for _ in range(frames)]


def test_noise_is_bounded_by_dir_noise_deg():
    enemy = _make()
    samples = _sample(enemy, 2000)
    assert max(abs(s) for s in samples) <= enemy.dir_noise_deg + 1e-9


def test_noise_drifts_slowly_and_covers_both_sides():
    enemy = _make()
    samples = _sample(enemy, 600)  # ~10 sek

    # Jevn: endrer seg lite per frame
    max_step = max(abs(b - a) for a, b in zip(samples, samples[1:]))
    assert max_step < 1.0
    # Men driver faktisk til begge sider over tid
    assert min(samples) < -5
    assert max(samples) > 5


def test_different_phases_give_different_noise():
    a = _make(phase=(0.0, 0.0))
    b = _make(phase=(2.0, 4.0))
    assert _sample(a, 60) != pytest.approx(_sample(b, 60))


def test_noise_fades_out_near_target():
    enemy = _make()
    assert all(s == 0 for s in _sample(enemy, 100, dist=0.4 * T))


def test_zero_dir_noise_deg_disables_noise():
    enemy = _make()
    enemy.dir_noise_deg = 0
    enemy.accel_time_ms = 0

    enemy._move_towards((enemy.pos.x + FAR, enemy.pos.y), [], DT)

    assert enemy.velocity.y == 0


def test_move_towards_direction_is_rotated_by_noise():
    enemy = _make(phase=(math.pi / 2, 0.0))  # gir tydelig positivt avvik ved start
    enemy.accel_time_ms = 0

    enemy._move_towards((enemy.pos.x + FAR, enemy.pos.y), [], DT)

    angle = math.degrees(math.atan2(enemy.velocity.y, enemy.velocity.x))
    assert 0 < abs(angle) <= enemy.dir_noise_deg


@pytest.mark.parametrize("phase", [(0.0, 0.0), (1.5, 3.0), (3.1, 5.5), (4.7, 2.2)])
def test_enemy_still_reaches_target(phase):
    enemy = _make(phase=phase)
    target = (enemy.pos.x + 6 * T, enemy.pos.y + 3 * T)

    reached = False
    for _ in range(60 * 10):  # maks 10 sek
        if enemy._move_towards(target, [], DT):
            reached = True
            break

    assert reached
