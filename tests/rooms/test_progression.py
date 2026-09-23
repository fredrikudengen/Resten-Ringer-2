from types import SimpleNamespace

from rooms.progression import (
    ENEMY_POOL,
    level_from_rooms_cleared,
    choose_enemy,
    scale_enemy,
)


def test_level_from_rooms_cleared_thresholds():
    assert level_from_rooms_cleared(0) == 1
    assert level_from_rooms_cleared(2) == 1
    assert level_from_rooms_cleared(3) == 2
    assert level_from_rooms_cleared(18) == 9
    assert level_from_rooms_cleared(19) == 10
    assert level_from_rooms_cleared(1000) == 10


def test_choose_enemy_only_returns_enemies_from_that_levels_pool():
    for level in range(1, 11):
        for _ in range(20):
            assert choose_enemy(level) in ENEMY_POOL[level]

    # Levels beyond the highest defined pool fall back to level 10's pool.
    assert choose_enemy(50) in ENEMY_POOL[10]


def test_scale_enemy_scales_health_and_damage_but_skips_level_1_and_bosses():
    melee = SimpleNamespace(health=100, damage=10)
    scale_enemy(melee, 1)
    assert melee.health == 100 and melee.damage == 10

    scale_enemy(melee, 5)
    assert melee.health == int(100 * 1.6)
    assert melee.damage == round(10 * 1.32, 1)

    ranged = SimpleNamespace(health=200, gun=SimpleNamespace(damage=20))
    scale_enemy(ranged, 10)
    assert ranged.health == int(200 * (1.0 + 9 * 0.15))
    assert ranged.gun.damage == round(20 * (1.0 + 9 * 0.08), 1)

    boss = SimpleNamespace(health=2000, damage=55, is_boss=True)
    scale_enemy(boss, 10)
    assert boss.health == 2000 and boss.damage == 55
