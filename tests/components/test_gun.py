import pygame

from components.gun import Pistol, Shotgun, SniperRifle

# Guns compare pygame.time.get_ticks() against an internal "last event"
# timestamp that starts at 0, so tests start the clock well past 0 to
# mirror how the game actually runs (ticks are already large by the time
# gameplay starts).
BASE_TICK = 100_000


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


def test_can_shoot_true_initially_then_false_until_fire_rate_elapses(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = Pistol()

    assert gun.can_shoot() is True

    bullets = gun.shoot((0, 0), pygame.math.Vector2(1, 0))
    assert len(bullets) == 1
    assert gun.can_shoot() is False

    _set_ticks(monkeypatch, BASE_TICK + gun.fire_rate_ms - 1)
    assert gun.can_shoot() is False

    _set_ticks(monkeypatch, BASE_TICK + gun.fire_rate_ms)
    assert gun.can_shoot() is True


def test_shooting_depletes_ammo_and_auto_starts_reload_at_zero(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = Pistol()
    assert gun.current_ammo == gun.max_ammo

    for i in range(gun.max_ammo):
        _set_ticks(monkeypatch, BASE_TICK + i * gun.fire_rate_ms)
        gun.shoot((0, 0), pygame.math.Vector2(1, 0))

    assert gun.current_ammo == 0
    assert gun.is_reloading is True


def test_update_reload_restores_ammo_only_after_reload_time_elapses(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = Pistol()
    gun.current_ammo = 0
    gun.start_reload()
    assert gun.is_reloading is True

    _set_ticks(monkeypatch, BASE_TICK + gun.reload_time_ms - 1)
    gun.update_reload()
    assert gun.is_reloading is True
    assert gun.current_ammo == 0

    _set_ticks(monkeypatch, BASE_TICK + gun.reload_time_ms)
    gun.update_reload()
    assert gun.is_reloading is False
    assert gun.current_ammo == gun.max_ammo


def test_reload_progress_reports_full_when_idle_and_clamped_while_reloading(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = Pistol()
    assert gun.reload_progress() == 1.0

    gun.current_ammo = 0
    gun.start_reload()
    assert gun.reload_progress() == 0.0

    _set_ticks(monkeypatch, BASE_TICK + gun.reload_time_ms // 2)
    mid = gun.reload_progress()
    assert 0.0 < mid < 1.0

    _set_ticks(monkeypatch, BASE_TICK + gun.reload_time_ms * 10)
    assert gun.reload_progress() == 1.0


def test_shotgun_fires_multiple_pellets_per_shot(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = Shotgun()

    bullets = gun.shoot((0, 0), pygame.math.Vector2(1, 0))

    assert len(bullets) == gun.pellets


def test_sniper_rifle_shot_is_piercing(monkeypatch):
    _set_ticks(monkeypatch, BASE_TICK)
    gun = SniperRifle()

    bullets = gun.shoot((0, 0), pygame.math.Vector2(1, 0))

    assert len(bullets) == 1
    assert bullets[0].piercing is True
