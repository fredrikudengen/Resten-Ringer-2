import pygame
from pygame.math import Vector2

from core import constants
from components.bullet import Bullet
from entities.enemies.boss_enemies import WardenBoss
from entities.enemies.elite_enemies import AssassinEnemy, BruteEnemy, ScoutEnemy, SlowEnemy, TankEnemy
from entities.enemies.enemy import Enemy
from entities.enemies.enemy_types import FastEnemy, MarksmanEnemy, ShooterEnemy, SwarmEnemy
from view.sprite import Sprite

DT = 16


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


class _TestEnemy(Enemy):
    name              = "test_enemy"
    speed             = 300
    health            = 100
    damage            = 5
    attack_cooldown   = 500
    knockback_strength= 6
    color             = (255, 0, 255)
    width             = 32
    height            = 32
    accel_time_ms     = 0
    dir_noise_deg     = 0
    flinch_ms         = 120


def _make(monkeypatch, now=1000):
    _set_ticks(monkeypatch, now)
    return _TestEnemy(500, 500)


def _hit_from_left(enemy, strength=4):
    source = pygame.Rect(0, 0, 8, 8)
    source.center = (enemy.rect.centerx - 20, enemy.rect.centery)
    enemy.on_hit(source, strength)


def test_on_hit_sets_hit_and_applies_knockback_away_from_source(monkeypatch):
    enemy = _make(monkeypatch)
    _hit_from_left(enemy, strength=4)

    assert enemy.hit
    assert enemy.knockback_velocity.x > 0
    assert enemy.knockback_velocity.length() == 4


def test_knockback_taken_mult_scales_weapon_knockback(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.knockback_taken_mult = 0.5
    _hit_from_left(enemy, strength=4)

    assert enemy.knockback_velocity.length() == 2


def test_on_hit_stops_enemy_and_flinches(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.velocity.update(enemy.speed, 0)

    _hit_from_left(enemy)

    assert enemy.velocity.length() == 0
    assert enemy._flinching()
    assert enemy._hurt()


def test_flinching_enemy_does_not_steer_towards_target(monkeypatch):
    enemy = _make(monkeypatch)
    _hit_from_left(enemy)

    _set_ticks(monkeypatch, 1000 + 50)
    enemy._move_towards((enemy.pos.x + 1000, enemy.pos.y), [], DT)

    assert enemy.velocity.length() == 0


def test_flinch_ends_after_flinch_ms(monkeypatch):
    enemy = _make(monkeypatch)
    _hit_from_left(enemy)

    _set_ticks(monkeypatch, 1000 + enemy.flinch_ms)
    assert not enemy._flinching()

    enemy._move_towards((enemy.pos.x + 1000, enemy.pos.y), [], DT)
    assert enemy.velocity.x > 0


def test_flinch_has_cooldown_against_stunlock(monkeypatch):
    enemy = _make(monkeypatch)
    _hit_from_left(enemy)

    # Nytt treff rett etter at stoppet er over, men innenfor cooldown
    t = 1000 + enemy.flinch_ms + 10
    _set_ticks(monkeypatch, t)
    enemy.velocity.update(enemy.speed, 0)
    _hit_from_left(enemy)

    assert not enemy._flinching()
    assert enemy.velocity.x == enemy.speed  # ikke stoppet
    assert enemy._hurt()                    # men viser fortsatt treff
    assert enemy.knockback_velocity.length() > 0

    # Etter cooldown kan den flinche igjen
    _set_ticks(monkeypatch, 1000 + enemy.flinch_ms + constants.ENEMY_FLINCH_COOLDOWN_MS)
    _hit_from_left(enemy)
    assert enemy._flinching()


def test_zero_flinch_ms_only_shows_hurt(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.flinch_ms = 0
    enemy.velocity.update(enemy.speed, 0)

    _hit_from_left(enemy)

    assert not enemy._flinching()
    assert enemy.velocity.x == enemy.speed
    assert enemy._hurt()


def test_is_moving_false_while_flinching(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.state = "chase"
    assert enemy._is_moving()

    _hit_from_left(enemy)
    assert not enemy._is_moving()


def test_hurt_visual_uses_tint_without_hurt_frame(monkeypatch):
    enemy = _make(monkeypatch)
    assert enemy._hurt_visual("idle") == ("idle", None)

    _hit_from_left(enemy)
    assert enemy._hurt_visual("idle") == ("idle", constants.ENEMY_HURT_TINT)


def test_hurt_visual_uses_hurt_frame_and_tint_together(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.sprite = Sprite(frames={"idle": "x", "hurt": "y"}, base_size=(32, 32))

    _hit_from_left(enemy)
    assert enemy._hurt_visual("idle") == ("hurt", constants.ENEMY_HURT_TINT)


def test_hurt_visual_lasts_flinch_ms_then_returns_to_normal(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.sprite = Sprite(frames={"idle": "x", "hurt": "y"}, base_size=(32, 32))
    _hit_from_left(enemy)

    _set_ticks(monkeypatch, 1000 + enemy.flinch_ms - 1)
    assert enemy._hurt_visual("idle")[0] == "hurt"

    _set_ticks(monkeypatch, 1000 + enemy.flinch_ms)
    assert enemy._hurt_visual("idle") == ("idle", None)


def test_hurt_visual_shown_on_every_hit_even_during_flinch_cooldown(monkeypatch):
    enemy = _make(monkeypatch)
    _hit_from_left(enemy)

    t = 1000 + enemy.flinch_ms + 10  # stoppet er over, men cooldown gjelder
    _set_ticks(monkeypatch, t)
    _hit_from_left(enemy)

    assert not enemy._flinching()
    _set_ticks(monkeypatch, t + enemy.flinch_ms - 1)
    assert enemy._hurt()


def test_hurt_visual_without_flinch_uses_flash_duration(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.flinch_ms = 0
    _hit_from_left(enemy)

    _set_ticks(monkeypatch, 1000 + constants.ENEMY_HURT_FLASH_MS - 1)
    assert enemy._hurt()
    _set_ticks(monkeypatch, 1000 + constants.ENEMY_HURT_FLASH_MS)
    assert not enemy._hurt()


def test_all_enemy_types_have_hurt_frame(monkeypatch):
    _set_ticks(monkeypatch, 1000)

    for cls in (FastEnemy, SwarmEnemy, ShooterEnemy, MarksmanEnemy, ScoutEnemy,
                AssassinEnemy, SlowEnemy, BruteEnemy, TankEnemy, WardenBoss):
        assert cls(500, 500).sprite.has_frame("hurt"), cls.__name__


class _OpenRoom:
    def is_blocked(self, gx, gy):
        return False


class _FakePlayer:
    def __init__(self, center):
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = center
        self.is_invincible = True  # ikke relevant her

    def _grid_pos(self):
        T = constants.TILE_SIZE
        return (self.rect.centerx // T, self.rect.centery // T)


def test_enemy_does_not_turn_around_when_knocked_back(monkeypatch):
    enemy = _make(monkeypatch)
    enemy.detection_radius = 10_000
    enemy.state = "chase"
    enemy.accel_time_ms = 250
    player = _FakePlayer((enemy.rect.centerx + 400, enemy.rect.centery))
    room = _OpenRoom()

    # Gå mot spilleren (til høyre) en stund
    for _ in range(20):
        enemy.move(player, [], room, DT)
    assert enemy.facing_left is False

    # Treff forfra med kraftig knockback mot venstre
    source = pygame.Rect(0, 0, 8, 8)
    source.center = (enemy.rect.centerx + 20, enemy.rect.centery)
    enemy.on_hit(source, 20)

    for i in range(10):
        _set_ticks(monkeypatch, 1000 + i * DT)
        start_x = enemy.pos.x
        enemy.move(player, [], room, DT)
        assert enemy.facing_left is False, f"snudde seg i frame {i}"
    assert enemy.pos.x < start_x + 1  # ble faktisk dyttet bakover / sto i ro


def test_elite_melee_enemies_turn_towards_movement(monkeypatch):
    _set_ticks(monkeypatch, 1000)
    room = _OpenRoom()

    for cls in (AssassinEnemy, SlowEnemy, BruteEnemy, TankEnemy):
        enemy = cls(2000, 500)
        enemy.state = "chase"
        enemy.detection_radius = 10_000
        enemy.dir_noise_deg = 0
        player = _FakePlayer((enemy.rect.centerx - 600, enemy.rect.centery))  # til venstre

        for _ in range(20):
            enemy.move(player, [], room, DT)

        assert enemy.facing_left is True, cls.__name__


def test_update_facing_follows_own_velocity_with_deadzone(monkeypatch):
    enemy = _make(monkeypatch)

    enemy.velocity.update(-100, 0)
    enemy._update_facing()
    assert enemy.facing_left is True

    enemy.velocity.update(2, 0)  # innenfor dødsonen – beholder retning
    enemy._update_facing()
    assert enemy.facing_left is True

    enemy.velocity.update(100, 0)
    enemy._update_facing()
    assert enemy.facing_left is False


def test_bullet_damage_enemy_triggers_hit_reaction(monkeypatch):
    enemy = _make(monkeypatch)
    bullet = Bullet(
        pos=(enemy.rect.centerx - 20, enemy.rect.centery),
        direction=Vector2(1, 0),
        speed=500, damage=10, radius=4, color=(255, 255, 255),
        max_range=1000, team="player", knockback_strength=3,
    )

    bullet.damage_enemy(enemy)

    assert enemy.health == 90
    assert enemy.hit
    assert enemy._flinching()
    assert enemy.knockback_velocity.x > 0
    assert not bullet.alive
