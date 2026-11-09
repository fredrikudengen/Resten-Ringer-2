import os

import pygame

from entities.enemies.elite_enemies import AssassinEnemy
from view.afterimage import AfterimageTrail

ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")


class _Camera:
    def apply(self, rect):
        return rect


class _RecordingSprite:
    def __init__(self):
        self.calls = []

    def draw(self, screen, draw_rect, **kwargs):
        self.calls.append((draw_rect.center, kwargs))


def test_trail_records_only_while_active_at_interval():
    trail = AfterimageTrail(interval_ms=30, lifetime_ms=1000)
    trail.update(False, (0, 0), "idle", False, 0)
    assert len(trail) == 0

    for t in range(0, 100, 10):
        trail.update(True, (t, 0), "lunge", False, t)
    assert len(trail) == 4  # t = 0, 30, 60, 90


def test_trail_ghosts_fade_and_expire():
    trail = AfterimageTrail(interval_ms=30, lifetime_ms=160, max_alpha=150)
    trail.update(True, (10, 20), "lunge", True, 0)
    trail.update(False, (99, 99), "idle", False, 80)

    sprite = _RecordingSprite()
    trail.draw(None, _Camera(), sprite, (32, 32), now=80)
    (center, kwargs), = sprite.calls
    assert center == (10, 20)
    assert kwargs["frame"] == "lunge" and kwargs["flip_x"] is True
    assert 0 < kwargs["alpha"] < 150

    trail.update(False, (99, 99), "idle", False, 160)
    assert len(trail) == 0


def test_assassin_has_windup_and_lunge_frames_on_disk():
    enemy = AssassinEnemy(0, 0)
    for frame in ("windup", "lunge"):
        assert enemy.sprite.has_frame(frame), frame
        path = enemy.sprite._animations[frame][0]
        assert os.path.isfile(os.path.join(ASSETS, path + ".png")), path


def test_assassin_frame_follows_lunge_state():
    enemy = AssassinEnemy(0, 0)
    for state, frame in (("chase", "idle"), ("lunge_windup", "windup"), ("lunge", "lunge")):
        enemy.state = state
        assert enemy._sprite_frame() == frame
