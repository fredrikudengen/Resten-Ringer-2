import random
from entities import (
    FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy, ShooterEnemy, MarksmanEnemy
)

# Antall rom ryddet → progression level
_THRESHOLDS = [2, 4, 6, 8, 10, 12, 14, 16, 18]

# Vektet pool per level – dupliserte entries = høyere sannsynlighet
ENEMY_POOL = {
    1:  [SwarmEnemy, SwarmEnemy, FastEnemy],
    2:  [SwarmEnemy, FastEnemy, FastEnemy],
    3:  [FastEnemy, FastEnemy, SlowEnemy],
    4:  [FastEnemy, SlowEnemy, ScoutEnemy, ShooterEnemy],
    5:  [FastEnemy, SlowEnemy, ScoutEnemy, AssassinEnemy, ShooterEnemy],
    6:  [FastEnemy, SlowEnemy, AssassinEnemy, TankEnemy, ShooterEnemy, MarksmanEnemy],
    7:  [SlowEnemy, AssassinEnemy, TankEnemy, BruteEnemy, ShooterEnemy, MarksmanEnemy],
    8:  [AssassinEnemy, AssassinEnemy, TankEnemy, BruteEnemy, ShooterEnemy, MarksmanEnemy, MarksmanEnemy],
    9:  [TankEnemy, TankEnemy, BruteEnemy, BruteEnemy, AssassinEnemy, ShooterEnemy, ShooterEnemy, MarksmanEnemy, MarksmanEnemy],
    10: [TankEnemy, BruteEnemy, BruteEnemy, AssassinEnemy, ShooterEnemy, ShooterEnemy, MarksmanEnemy, MarksmanEnemy]
}


def level_from_rooms_cleared(rooms_cleared: int) -> int:
    """Beregn progression level basert på antall ryddede rom."""
    for level, threshold in enumerate(_THRESHOLDS, start=1):
        if rooms_cleared <= threshold:
            return level
    return 10


def choose_enemy(progression_level: int):
    """Velg en tilfeldig enemy class basert på progression level."""
    pool = ENEMY_POOL.get(min(progression_level, 10), ENEMY_POOL[10])
    return random.choice(pool)


def scale_enemy(enemy, progression_level: int):
    """
    Apply a stat multiplier to a freshly spawned enemy based on progression level.

    HP scales faster than damage so rooms feel meatier without suddenly
    one-shotting the player. Both curves are tuned so that player level-up
    bonuses comfortably outpace enemy growth.

    Level 1:  1.00x HP, 1.00x dmg  (baseline)
    Level 5:  1.60x HP, 1.32x dmg
    Level 10: 2.35x HP, 1.72x dmg
    """
    if progression_level <= 1:
        return enemy

    hp_mult  = 1.0 + (progression_level - 1) * 0.15
    dmg_mult = 1.0 + (progression_level - 1) * 0.08

    # TODO: fix enemy scaling
    enemy.health = int(enemy.health * hp_mult)
    enemy.damage = round(enemy.damage * dmg_mult, 1)
    return enemy