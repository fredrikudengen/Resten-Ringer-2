import pygame

from view.sprite import Sprite
from fakes import set_ticks


def _sprite(**kw):
    return Sprite(
        frames={"windup": ["w0", "w1", "w2"], "walk": ["a", "b"], "idle": "i"},
        base_size=(32, 32),
        frame_durations={"windup": 100, "walk": 100},
        **kw,
    )


def _show(sprite, state, monkeypatch, now):
    """Som draw(): velg frame og husk hvilken state som sist ble vist."""
    set_ticks(monkeypatch, now)
    path = sprite._current_path(state)
    sprite._last_frame_name = state
    return path


def test_looping_animation_wraps_around(monkeypatch):
    sprite = _sprite()
    seen = [_show(sprite, "walk", monkeypatch, t) for t in (0, 100, 200, 300)]
    assert seen == ["a", "b", "a", "b"]


def test_play_once_holds_last_frame(monkeypatch):
    sprite = _sprite(play_once={"windup"})
    seen = [_show(sprite, "windup", monkeypatch, t) for t in (0, 100, 200, 300, 400)]
    assert seen == ["w0", "w1", "w2", "w2", "w2"]


def test_animation_restarts_when_shown_again(monkeypatch):
    sprite = _sprite(play_once={"windup"})
    for t in (0, 100, 200):
        _show(sprite, "windup", monkeypatch, t)
    _show(sprite, "idle", monkeypatch, 300)
    assert _show(sprite, "windup", monkeypatch, 5000) == "w0"
