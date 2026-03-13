import random
from entities import (
    FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy
)

# Antall rom ryddet → progression level
_THRESHOLDS = [2, 4, 6, 8, 10, 12, 14, 16, 18]

# Vektet pool per level – dupliserte entries = høyere sannsynlighet
ENEMY_POOL = {
    1:  [SwarmEnemy, SwarmEnemy, FastEnemy],
    2:  [SwarmEnemy, FastEnemy, FastEnemy],
    3:  [FastEnemy, FastEnemy, SlowEnemy],
    4:  [FastEnemy, SlowEnemy, ScoutEnemy],
    5:  [FastEnemy, SlowEnemy, ScoutEnemy, AssassinEnemy],
    6:  [FastEnemy, SlowEnemy, AssassinEnemy, TankEnemy],
    7:  [SlowEnemy, AssassinEnemy, TankEnemy, BruteEnemy],
    8:  [AssassinEnemy, AssassinEnemy, TankEnemy, BruteEnemy],
    9:  [TankEnemy, TankEnemy, BruteEnemy, BruteEnemy, AssassinEnemy],
    10: [TankEnemy, BruteEnemy, BruteEnemy, AssassinEnemy],
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