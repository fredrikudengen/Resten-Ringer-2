import os

import pygame

from core import constants
from entities.enemies.elite_enemies import SlowEnemy, BruteEnemy, TankEnemy, WindupMeleeMixin

DT = 16
MELEE = (SlowEnemy, BruteEnemy, TankEnemy)
ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")


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


def test_melee_sprites_have_windup_and_strike_frames_on_disk():
    for cls in MELEE:
        enemy = cls(0, 0)
        for frame in ("windup", "strike"):
            assert enemy.sprite.has_frame(frame), (cls.__name__, frame)
            path = enemy.sprite._animations[frame][0]
            assert os.path.isfile(os.path.join(ASSETS, path + ".png")), path


def test_windup_frame_during_attack_then_strike_then_idle(monkeypatch):
    for cls in MELEE:
        enemy = _make(cls, monkeypatch)
        player = _FakePlayer((enemy.rect.centerx + 40, enemy.rect.centery))
        room = _OpenRoom()

        assert enemy._sprite_frame() == "idle"

        enemy.move(player, [], room, DT)
        assert enemy.state == "attack", cls.__name__
        assert enemy._sprite_frame() == "windup"

        hit_at = 1000 + cls.attack_windup_ms
        _set_ticks(monkeypatch, hit_at)
        enemy.move(player, [], room, DT)
        assert enemy.state == "chase"
        assert enemy._sprite_frame() == "strike", cls.__name__

        _set_ticks(monkeypatch, hit_at + WindupMeleeMixin._STRIKE_MS - 1)
        assert enemy._sprite_frame() == "strike"

        _set_ticks(monkeypatch, hit_at + WindupMeleeMixin._STRIKE_MS)
        assert enemy._sprite_frame() == "idle"


def test_brute_lunge_uses_windup_and_strike_frames(monkeypatch):
    enemy = _make(BruteEnemy, monkeypatch)
    player = _FakePlayer((enemy.rect.centerx + 250, enemy.rect.centery))

    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "lunge_windup"
    assert enemy._sprite_frame() == "windup"

    _set_ticks(monkeypatch, 1000 + BruteEnemy._LUNGE_WINDUP + 1)
    enemy.move(player, [], _OpenRoom(), DT)
    assert enemy.state == "lunge"
    assert enemy._sprite_frame() == "strike"
