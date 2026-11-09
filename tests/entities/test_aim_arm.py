import math
import os

import pygame
from pygame.math import Vector2

from entities.enemies.enemy_types import MarksmanEnemy, ShooterEnemy
from entities.player import Player
from view.aim_arm import AimArm

ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


def test_muzzle_follows_rotation_and_flip():
    arm = AimArm("x", scale=2, pivot=(0, 5), muzzle=(14, 1))
    # Mot høyre: 28 px frem, 8 px opp (munningen ligger 4 kildepiksler over pivot)
    assert arm.muzzle((100, 100), 0, False) == (128, 92)
    # Rett opp: x-avviket blir til venstre, lengden til opp
    assert arm.muzzle((100, 100), 90, False) == (92, 72)
    # Flippet mot venstre: munningen fortsatt over pivot
    mx, my = arm.muzzle((100, 100), 180, True)
    assert (mx, my) == (72, 92)


def test_shoulder_mirrors_when_flipped():
    arm = AimArm("x", scale=3, pivot=(0, 0), muzzle=(0, 0), shoulder=(2, 1))
    assert arm.shoulder((50, 50), False) == (56, 53)
    assert arm.shoulder((50, 50), True) == (44, 53)


def test_player_muzzle_matches_previous_formula():
    player = Player()
    s = player.width / 32
    player._shoulder_world = (300, 200)
    for flip in (False, True):
        for angle in (0, 37, 120, -75, 180):
            player.flip_x, player.aim_angle = flip, angle
            old = Vector2(14 * s, (-4 if flip else 4) * s).rotate(angle)
            assert player.muzzle_pos == (int(300 + old.x), int(200 - old.y))


def test_gunmen_have_arm_sprites_on_disk():
    for cls in (ShooterEnemy, MarksmanEnemy):
        assert cls.arm_sprite, cls.__name__
        assert os.path.isfile(os.path.join(ASSETS, cls.arm_sprite + ".png")), cls.arm_sprite


def test_arm_aims_at_target_and_relaxes_without_one(monkeypatch):
    _set_ticks(monkeypatch, 1000)
    enemy = ShooterEnemy(2000, 2000)
    enemy._aim_offset_deg = 0.0

    sx, sy = enemy._shoulder_world()
    enemy._aim_target = (sx, sy - 100)                   # rett over skulderen
    assert abs(enemy.aim_angle() - 90) < 1e-6

    enemy._aim_offset_deg = 5.0                           # avviket vises på armen
    assert abs(enemy.aim_angle() - 85) < 1e-6

    enemy._aim_target = None
    enemy.facing_left = False
    assert enemy.aim_angle() == enemy._RELAXED_ARM_DEG
    enemy.facing_left = True
    assert enemy.aim_angle() == 180 - enemy._RELAXED_ARM_DEG


def test_bullet_leaves_from_muzzle_not_center(monkeypatch):
    _set_ticks(monkeypatch, 1000)
    enemy = ShooterEnemy(2000, 2000)
    enemy.gun.spread = 0
    monkeypatch.setattr(enemy, "_next_aim_offset", lambda: 0.0)

    target = (enemy.rect.centerx + 300, enemy.rect.centery)
    enemy._do_shoot(target)

    bullet = enemy.pending_bullets[0]
    shoulder = enemy._shoulder_world()
    angle = math.degrees(math.atan2(-(target[1] - shoulder[1]), target[0] - shoulder[0]))
    expected = enemy.arm.muzzle(shoulder, angle, False)
    assert (round(bullet.pos.x), round(bullet.pos.y)) != enemy.rect.center
    assert abs(bullet.pos.x - expected[0]) <= 1 and abs(bullet.pos.y - expected[1]) <= 1
