import pygame
import pytest

from view.sprite import Sprite

GAIT = {"walk": {"cycle_ms": 400, "bounce": 14, "sway": 2, "lean": 3}}


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


def _sprite():
    return Sprite(frames={"walk": ["a", "b"]}, base_size=(32, 32), gait=GAIT)


def test_gait_phase_overrides_clock(monkeypatch):
    sprite = _sprite()
    _set_ticks(monkeypatch, 12345)  # vilkårlig klokke – skal ikke spille noen rolle

    _, _, bounce_start, _ = sprite._gait_frame("walk", phase=0.0)
    _, _, bounce_peak, _ = sprite._gait_frame("walk", phase=0.25)
    _, _, bounce_end, _ = sprite._gait_frame("walk", phase=0.5)

    assert bounce_start == 0
    assert bounce_peak == -14
    assert bounce_end == 0


def test_gait_phase_selects_frame_by_half_step():
    sprite = _sprite()
    assert sprite._gait_frame("walk", phase=0.1)[0] == "a"
    assert sprite._gait_frame("walk", phase=0.4)[0] == "b"


def test_without_gait_phase_uses_clock(monkeypatch):
    sprite = _sprite()
    _set_ticks(monkeypatch, 1000)
    sprite._last_frame_name = "walk"
    sprite._gait_frame("walk")  # starter syklusen ved t=1000

    _set_ticks(monkeypatch, 1100)  # 100ms = kvart syklus → topp
    _, _, bounce, _ = sprite._gait_frame("walk")
    assert bounce == -14


def test_standing_still_resets_gait_cycle(monkeypatch):
    sprite = _sprite()
    _set_ticks(monkeypatch, 1000)
    sprite._resolve_frame("walk", False, 0, 0.0, moving=True)
    sprite._last_frame_name = "walk"

    _set_ticks(monkeypatch, 1100)
    sprite._resolve_frame("walk", False, 0, 0.0, moving=False)
    assert "walk" not in sprite._gait_phase_start

    # Neste bevegelse starter på fase 0 – ingen hopp midt i en sprett
    _set_ticks(monkeypatch, 5000)
    _, _, bounce, _ = sprite._resolve_frame("walk", False, 0, 0.0, moving=True)
    assert bounce == 0


@pytest.mark.parametrize("flip", [False, True])
def test_gait_phase_passes_through_resolve_frame(flip):
    sprite = _sprite()
    _, _, bounce, _ = sprite._resolve_frame("walk", flip, 0, 0.0, moving=True, gait_phase=0.25)
    assert bounce == -14
