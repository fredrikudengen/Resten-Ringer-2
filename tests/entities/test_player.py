import pygame

from core import constants
from entities.player import Player


def _set_ticks(monkeypatch, value: int):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: value)


def test_xp_to_next_follows_the_xp_scale_formula():
    player = Player()

    for level, expected in (
        (1, constants.XP_BASE),
        (2, int(constants.XP_BASE * constants.XP_SCALE)),
        (3, int(constants.XP_BASE * constants.XP_SCALE ** 2)),
    ):
        player.level = level
        assert player.xp_to_next == expected


def test_gain_xp_levels_up_and_keeps_leftover_xp():
    player = Player()
    to_next = player.xp_to_next

    player.gain_xp(to_next + 10)

    assert player.level == 2
    assert player.xp == 10


def test_gain_xp_can_trigger_multiple_level_ups_in_one_call():
    player = Player()
    total = player.xp_to_next  # to reach level 2
    total += int(constants.XP_BASE * constants.XP_SCALE)  # to reach level 3

    player.gain_xp(total)

    assert player.level == 3
    assert player.xp == 0


def test_level_up_grants_health_and_damage_bonuses():
    player = Player()
    start_health = player.health
    start_max_health = player.max_health
    start_damage = player.gun.damage

    player._level_up()

    assert player.level == 2
    assert player.health == start_health + constants.XP_HP_BONUS_PER_LEVEL
    assert player.max_health == start_max_health + constants.XP_HP_BONUS_PER_LEVEL
    assert player.gun.damage == start_damage + constants.XP_DPS_BONUS_PER_LEVEL


def test_apply_attack_powerup_increases_damage_and_reverts_after_duration(monkeypatch):
    _set_ticks(monkeypatch, 0)
    player = Player()
    base_damage = player.gun.damage

    player.apply_powerup("AttackPowerup")
    _, pct = constants.BUFF_VALUES["AttackPowerup"]
    bonus = int(base_damage * pct)
    assert player.gun.damage == base_damage + bonus

    duration = constants.BUFF_DURATIONS["AttackPowerup"]
    _set_ticks(monkeypatch, duration - 1)
    player.update_powerups()
    assert player.gun.damage == base_damage + bonus

    _set_ticks(monkeypatch, duration)
    player.update_powerups()
    assert player.gun.damage == base_damage


def test_apply_attack_powerup_twice_while_active_is_a_no_op(monkeypatch):
    _set_ticks(monkeypatch, 0)
    player = Player()
    base_damage = player.gun.damage

    player.apply_powerup("AttackPowerup")
    once_applied = player.gun.damage

    player.apply_powerup("AttackPowerup")
    assert player.gun.damage == once_applied != base_damage


def test_apply_health_powerup_heals_but_caps_at_max_health_and_has_no_timer():
    player = Player()
    player.health = player.max_health - 5

    player.apply_powerup("HealthPowerup")

    assert player.health == player.max_health
    assert "HealthPowerup" not in player.buff_timers
