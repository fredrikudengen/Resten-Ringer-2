"""Låser oppførselen til fiendenes tilstandsmaskiner (move()) på tvers av fiendetypene.

Dekker overgangene som er felles (død, treff, sansing, idle/chase/search) og det som
skiller typene (kontaktskade, windup-slag, skyting/reload, scout som alltid jager, bossens daze).
"""
import pygame

from entities.enemies.boss_enemies import WardenBoss
from entities.enemies.elite_enemies import ScoutEnemy, SlowEnemy
from entities.enemies.enemy_types import FastEnemy, ShooterEnemy
from fakes import set_ticks, OpenRoom, FakePlayer

DT = 16
FAR = 5000  # langt utenfor alle detection_radius


def _make(cls, monkeypatch, now=1000, state="idle"):
    set_ticks(monkeypatch, now)
    monkeypatch.setattr(cls, "stat_spread", 0)
    enemy = cls(2000, 2000)
    enemy.state = state
    enemy.dir_noise_deg = 0
    enemy.next_wander_at = 10**9  # ingen tilfeldig vandring
    return enemy


def _player(enemy, dx, **kw):
    return FakePlayer((enemy.rect.centerx + dx, enemy.rect.centery), **kw)


def _step(enemy, player, monkeypatch, now):
    set_ticks(monkeypatch, now)
    enemy.move(player, [], OpenRoom(), DT)


# ---------- felles for alle ----------

def test_enemies_die_when_health_runs_out(monkeypatch):
    for cls in (FastEnemy, SlowEnemy, ShooterEnemy, ScoutEnemy, WardenBoss):
        enemy = _make(cls, monkeypatch, state="chase")
        enemy.health = 0
        _step(enemy, _player(enemy, 100), monkeypatch, 1000)
        assert enemy.state == "dead" and enemy.alive is False, cls.__name__


def test_melee_enemy_hit_while_idle_starts_searching(monkeypatch):
    for cls in (FastEnemy, SlowEnemy):
        enemy = _make(cls, monkeypatch)
        enemy.hit = True
        player = _player(enemy, FAR)
        _step(enemy, player, monkeypatch, 1000)
        assert enemy.state == "search", cls.__name__
        assert enemy.hit is False
        assert enemy.last_seen_pos == player.rect.center
        assert enemy.search_started == 1000


def test_hit_while_chasing_does_not_change_state(monkeypatch):
    for cls in (FastEnemy, SlowEnemy):
        enemy = _make(cls, monkeypatch, state="chase")
        enemy.hit = True
        _step(enemy, _player(enemy, 300), monkeypatch, 1000)
        assert enemy.state == "chase", cls.__name__
        assert enemy.hit is True


def test_chasing_enemy_that_loses_sight_searches_last_seen_pos(monkeypatch):
    for cls in (FastEnemy, SlowEnemy, ShooterEnemy):
        enemy = _make(cls, monkeypatch, state="chase")
        enemy.last_seen_pos = (1, 1)
        _step(enemy, _player(enemy, FAR), monkeypatch, 1234)
        assert enemy.state == "search", cls.__name__
        assert enemy.search_started == 1234


def test_chasing_enemy_without_last_seen_pos_goes_idle(monkeypatch):
    for cls in (FastEnemy, SlowEnemy, ShooterEnemy):
        enemy = _make(cls, monkeypatch, state="chase")
        _step(enemy, _player(enemy, FAR), monkeypatch, 1000)
        assert enemy.state == "idle", cls.__name__


def test_searching_enemy_that_sees_player_chases(monkeypatch):
    for cls in (FastEnemy, SlowEnemy, ShooterEnemy):
        enemy = _make(cls, monkeypatch, state="search")
        enemy.last_seen_pos = (1, 1)
        _step(enemy, _player(enemy, 300), monkeypatch, 1000)
        assert enemy.state == "chase", cls.__name__


def test_debug_los_is_set_when_player_within_detection(monkeypatch):
    # Windup-fiendene (SlowEnemy) satte ikke _debug_los før tilstandsmaskinen ble felles
    for cls in (FastEnemy, SlowEnemy):
        enemy = _make(cls, monkeypatch, state="chase")
        player = _player(enemy, 300)
        _step(enemy, player, monkeypatch, 1000)
        assert enemy._debug_los == player.rect.center, cls.__name__


# ---------- vanlig melee: kontaktskade ----------

def test_contact_damage_sets_cooldown_and_pushes_enemy_back(monkeypatch):
    enemy = _make(FastEnemy, monkeypatch, state="chase")
    player = _player(enemy, 10)
    _step(enemy, player, monkeypatch, 1000)

    assert player.health == 1000 - FastEnemy.damage
    assert enemy.attack_cooldown_until == 1000 + FastEnemy.attack_cooldown
    assert enemy.knockback_velocity.x < 0  # dyttet bort fra spilleren (som står til høyre)


# ---------- windup-melee ----------

def test_windup_enemy_misses_if_player_left_range(monkeypatch):
    enemy = _make(SlowEnemy, monkeypatch, state="chase")
    player = _player(enemy, 40)
    _step(enemy, player, monkeypatch, 1000)
    assert enemy.state == "attack"

    player.rect.centerx += 500
    _step(enemy, player, monkeypatch, 1000 + SlowEnemy.attack_windup_ms)
    assert enemy.state == "chase"
    assert player.health == 1000
    assert enemy.attack_cooldown_until == 1000 + SlowEnemy.attack_windup_ms + SlowEnemy.attack_cooldown


# ---------- skytter ----------

def test_ranged_enemy_hit_does_not_change_state(monkeypatch):
    for state in ("idle", "shoot"):
        enemy = _make(ShooterEnemy, monkeypatch, state=state)
        enemy.hit = True
        player = _player(enemy, FAR)
        _step(enemy, player, monkeypatch, 1000)
        assert enemy.state == ("idle" if state == "idle" else "chase")
        assert enemy.hit is False
        assert enemy.last_seen_pos == player.rect.center


def test_ranged_enemy_idle_reacts_to_chase_and_forgets_reposition(monkeypatch):
    enemy = _make(ShooterEnemy, monkeypatch)
    enemy._reposition_target = (5, 5)
    player = _player(enemy, 300)
    _step(enemy, player, monkeypatch, 1000)
    _step(enemy, player, monkeypatch, 1000 + int(enemy.reaction_ms) + 1)
    assert enemy.state == "chase"
    assert enemy._reposition_target is None


def test_ranged_enemy_leaves_reload_when_gun_is_ready(monkeypatch):
    for dx, expected in ((300, "chase"), (FAR, "search")):
        enemy = _make(ShooterEnemy, monkeypatch, state="reload")
        enemy.last_seen_pos = (1, 1)
        _step(enemy, _player(enemy, dx), monkeypatch, 1000)
        assert enemy.state == expected


def test_ranged_enemy_ticks_reload_before_dying(monkeypatch):
    enemy = _make(ShooterEnemy, monkeypatch, state="chase")
    calls = []
    monkeypatch.setattr(enemy.gun, "update_reload", lambda: calls.append(1))
    enemy.health = 0
    _step(enemy, _player(enemy, 300), monkeypatch, 1000)
    assert calls == [1]


# ---------- scout ----------

def test_scout_chases_without_detection_and_ignores_hit(monkeypatch):
    enemy = _make(ScoutEnemy, monkeypatch, state="idle")
    enemy.accel_time_ms = 0
    enemy.hit = True
    start_x = enemy.pos.x
    _step(enemy, _player(enemy, FAR), monkeypatch, 1000)
    assert enemy.hit is False
    assert enemy.state == "idle"           # scouten bytter aldri state, den bare jager
    assert enemy.pos.x > start_x


def test_scout_contact_damage(monkeypatch):
    enemy = _make(ScoutEnemy, monkeypatch)
    player = _player(enemy, 10)
    _step(enemy, player, monkeypatch, 1000)
    assert player.health == 1000 - ScoutEnemy.damage
    assert enemy.attack_cooldown_until == 1000 + ScoutEnemy.attack_cooldown


# ---------- boss ----------

def _boss(monkeypatch, state="chase"):
    boss = _make(WardenBoss, monkeypatch, state=state)
    boss._next_spawn_at = 10**9
    return boss


def test_boss_stays_dazed_and_still(monkeypatch):
    boss = _boss(monkeypatch, state="dazed")
    boss._daze_until = 5000
    start = pygame.Vector2(boss.pos)
    _step(boss, _player(boss, 300), monkeypatch, 2000)
    assert boss.state == "dazed"
    assert boss.pos == start


def test_boss_starts_lunge_windup_when_cooldown_is_over(monkeypatch):
    boss = _boss(monkeypatch)
    boss._lunge_cooldown_until = 0
    _step(boss, _player(boss, 600), monkeypatch, 1000)
    assert boss.state == "lunge_windup"
    assert boss._lunge_windup_until == 1000 + 1500


def test_boss_prefers_windup_attack_in_range(monkeypatch):
    boss = _boss(monkeypatch)
    boss._lunge_cooldown_until = 0
    _step(boss, _player(boss, 60), monkeypatch, 1000)
    assert boss.state == "attack"
    assert boss.attack_windup_until == 1000 + WardenBoss.attack_windup_ms


def test_boss_chases_without_line_of_sight_or_detection(monkeypatch):
    boss = _boss(monkeypatch)
    boss._lunge_cooldown_until = 10**9
    boss.accel_time_ms = 0
    start_x = boss.pos.x
    _step(boss, _player(boss, FAR), monkeypatch, 1000)
    assert boss.state == "chase"
    assert boss.pos.x > start_x


def test_boss_wall_hit_dazes_longer_than_max_distance(monkeypatch):
    boss = _boss(monkeypatch, state="lunge")
    boss._lunge_direction = pygame.Vector2(1, 0)
    boss._lunge_start = pygame.Vector2(boss.pos) - pygame.Vector2(WardenBoss._LUNGE_MAX_DIST + 1, 0)
    _step(boss, _player(boss, FAR), monkeypatch, 1000)
    assert boss.state == "dazed" and boss._daze_until == 1000 + WardenBoss._DAZE_DURATION

    boss = _boss(monkeypatch, state="lunge")
    boss._lunge_direction = pygame.Vector2(1, 0)
    boss._lunge_start = pygame.Vector2(boss.pos)
    wall = pygame.Rect(boss.rect.right, boss.rect.top, 50, boss.rect.height)
    set_ticks(monkeypatch, 1000)
    boss.move(_player(boss, -FAR), [wall], OpenRoom(), DT)
    assert boss.state == "dazed" and boss._daze_until == 1000 + WardenBoss._DAZE_DURATION_WALL
