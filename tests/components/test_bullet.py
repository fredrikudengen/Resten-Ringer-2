import pygame

from components.bullet import Bullet
from entities.player import Player


def _make_bullet(damage):
    return Bullet(
        pos=(0, 0),
        direction=pygame.math.Vector2(1, 0),
        speed=0,
        damage=damage,
        radius=4,
        color=(255, 255, 255),
        max_range=100,
        team="enemy",
        knockback_strength=0,
    )


def test_damage_player_depletes_shield_before_health():
    player = Player()
    player.shield = 10
    start_health = player.health

    bullet = _make_bullet(6)
    bullet.damage_player(player)

    assert player.shield == 4
    assert player.health == start_health


def test_damage_player_spills_over_into_health_once_shield_is_exhausted():
    player = Player()
    player.shield = 5
    start_health = player.health

    bullet = _make_bullet(12)
    bullet.damage_player(player)

    assert player.shield == 0
    assert player.health == start_health - 7


def test_damage_player_without_shield_hits_health_directly():
    player = Player()
    start_health = player.health

    bullet = _make_bullet(8)
    bullet.damage_player(player)

    assert player.shield == 0
    assert player.health == start_health - 8
