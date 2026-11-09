import pygame

from entities.enemies.boss_enemies import WardenBoss
from fakes import set_ticks, FakePlayer

DT = 16


def _make(monkeypatch, now=1000):
    set_ticks(monkeypatch, now)
    boss = WardenBoss(2000, 2000)
    boss._next_spawn_at = 10**9  # ingen minions i testene
    return boss


def test_lunge_cooldown_after_daze_is_relative_to_now_in_both_phases(monkeypatch):
    for phase, cooldown in ((1, WardenBoss._PHASE1_LUNGE_COOLDOWN), (2, WardenBoss._PHASE2_LUNGE_COOLDOWN)):
        boss = _make(monkeypatch, now=50_000)
        boss._phase = phase
        boss.state = "dazed"
        boss._daze_until = 49_000
        player = FakePlayer((boss.rect.centerx + 500, boss.rect.centery), health=10_000)

        boss.move(player, [], None, DT)

        assert boss.state == "chase"
        assert boss._lunge_cooldown_until == 50_000 + cooldown, f"fase {phase}"


def test_lunge_damages_player_only_once(monkeypatch):
    boss = _make(monkeypatch)
    player = FakePlayer(boss.rect.center, health=10_000)
    boss.state = "lunge"
    boss._lunge_direction = pygame.Vector2(1, 0)
    boss._lunge_start = pygame.Vector2(boss.pos)
    start_health = player.health

    t = 1000
    for _ in range(10):
        t += DT
        set_ticks(monkeypatch, t)
        player.rect.center = boss.rect.center  # spilleren blir stående inni bossen
        boss.move(player, [], None, DT)

    assert start_health - player.health == int(boss.damage * 1.5)


def test_lunge_starts_safely_when_standing_on_player(monkeypatch):
    boss = _make(monkeypatch)
    player = FakePlayer(boss.rect.center, health=10_000)
    boss.state = "lunge_windup"
    boss._lunge_windup_until = 0
    boss._lunge_hit = True

    boss.move(player, [], None, DT)  # krasjet tidligere med ValueError fra normalize()

    assert boss.state == "lunge"
    assert boss._lunge_direction.length() == 1
    assert boss._lunge_hit is False


def test_hud_fonts_are_created_once(monkeypatch):
    from src.view import fonts  # samme modul som koden bruker (ikke view.fonts)
    calls = []
    real_sysfont = pygame.font.SysFont
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **k: calls.append(a) or real_sysfont(*a, **k))
    fonts.font.cache_clear()

    boss = _make(monkeypatch)
    screen = pygame.Surface((800, 600))
    for _ in range(3):
        boss._draw_boss_hud(screen)

    assert len(calls) == 2
