import pytest

from core import constants
from entities.enemies.enemy import Enemy

T = constants.TILE_SIZE
DT = 16
FAR = 20 * T


class _BurstEnemy(Enemy):
    name              = "burst_enemy"
    speed             = 300
    health            = 40
    damage            = 5
    attack_cooldown   = 500
    knockback_strength= 6
    color             = (255, 0, 255)
    width             = 32
    height            = 32
    accel_time_ms     = 0      # instant, så fasene er lette å lese av farten
    dir_noise_deg     = 0
    burst_move_ms     = 200
    burst_pause_ms    = 100
    burst_jitter      = 0


def _make():
    enemy = _BurstEnemy(500, 500)
    # Deterministisk start: helt i begynnelsen av et hopp
    enemy._burst_moving = True
    enemy._burst_hops = 0
    enemy._burst_phase_len = enemy.burst_move_ms
    enemy._burst_left_ms = enemy.burst_move_ms
    return enemy


def _step(enemy):
    enemy._move_towards((enemy.pos.x + FAR, enemy.pos.y), [], DT)
    enemy.coast([], DT)


def test_burst_is_off_by_default():
    class _Plain(_BurstEnemy):
        burst_move_ms = 0
    enemy = _Plain(500, 500)

    assert not enemy._bursting()
    for _ in range(100):
        _step(enemy)
        assert enemy.velocity.x == enemy.speed
    assert enemy._gait_phase() is None


def test_alternates_between_move_and_pause():
    enemy = _make()
    moving = []
    for _ in range(60):
        _step(enemy)
        moving.append(enemy.velocity.x > 0)

    # 200ms hopp ≈ 12-13 frames, 100ms pause ≈ 6-7 frames
    assert moving[:12] == [True] * 12
    assert moving[13:18] == [False] * 5
    assert moving[20:30] == [True] * 10


def test_phase_lengths_follow_settings():
    enemy = _make()
    frames_moving = frames_paused = 0
    for _ in range(int(3000 / DT)):  # 3 sek = 10 hele sykluser
        _step(enemy)
        if enemy._burst_moving:
            frames_moving += 1
        else:
            frames_paused += 1

    ratio = frames_moving / (frames_moving + frames_paused)
    assert ratio == pytest.approx(200 / 300, abs=0.03)


def test_pause_brakes_with_inertia():
    enemy = _make()
    enemy.accel_time_ms = 200
    enemy.velocity.update(enemy.speed, 0)
    enemy._burst_moving = False
    enemy._burst_phase_len = enemy._burst_left_ms = 100

    enemy._move_towards((enemy.pos.x + FAR, enemy.pos.y), [], DT)

    # Bremser, men stopper ikke brått
    assert 0 < enemy.velocity.x < enemy.speed


def test_jitter_varies_phase_lengths_within_bounds():
    enemy = _make()
    enemy.burst_jitter = 0.25
    lengths = [enemy._burst_phase_length(True) for _ in range(500)]

    assert min(lengths) >= 200 * 0.75
    assert max(lengths) <= 200 * 1.25
    assert len(set(lengths)) > 1


def test_is_moving_false_during_pause():
    enemy = _make()
    enemy.state = "chase"
    assert enemy._is_moving()

    enemy._burst_moving = False
    assert not enemy._is_moving()


def test_gait_phase_spans_one_bounce_per_hop():
    enemy = _make()
    assert enemy._gait_phase() == pytest.approx(0.0)

    enemy._burst_left_ms = enemy._burst_phase_len / 2
    assert enemy._gait_phase() == pytest.approx(0.25)

    enemy._burst_left_ms = 0
    assert enemy._gait_phase() == pytest.approx(0.5)

    # Neste hopp fortsetter i andre halvdel av syklusen
    enemy._burst_hops = 1
    enemy._burst_left_ms = enemy._burst_phase_len
    assert enemy._gait_phase() == pytest.approx(0.5)


def test_gait_phase_none_during_pause():
    enemy = _make()
    enemy._burst_moving = False
    assert enemy._gait_phase() is None


def test_enemies_start_desynced():
    lefts = {round(_BurstEnemy(500, 500)._burst_left_ms, 3) for _ in range(20)}
    assert len(lefts) > 1
