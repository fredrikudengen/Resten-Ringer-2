import random
from entities import (
    FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy, ShooterEnemy, MarksmanEnemy
)

# ===========================================================================
# PROGRESJON — Vanskelighetsgrad og fiendepooler
# ===========================================================================
#
# Progression level bestemmer hvilke fiender som spawner og hvor sterke de er.
# Level øker basert på antall rom spilleren har ryddet.
#
# For å gjøre spillet lettere: senk dmg_mult og hp_mult i scale_enemy()
# For å gjøre spillet vanskeligere: øk dem, eller legg til farligere fiender
#                                   tidligere i ENEMY_POOL
# ===========================================================================

# Antall ryddede rom som trengs for å nå hvert progression level.
# Eksempel: etter 2 rom → level 1, etter 4 rom → level 2, osv.
# Legg til flere terskler for å forlenge progresjonskurven.
_THRESHOLDS = [2, 4, 6, 8, 10, 12, 14, 16, 18]

# ---------------------------------------------------------------------------
# Fiendepooler per progression level
# ---------------------------------------------------------------------------
# Hver liste inneholder de fiendene som kan spawne på det nivået.
# Dupliserte entries = høyere sannsynlighet for den fienden.
# Eksempel: [SwarmEnemy, SwarmEnemy, FastEnemy] → 2/3 sjanse for Swarm
#
# Ideer til nye fiender? Legg dem inn her og i enemy_types.py / elite_enemies.py!
# ---------------------------------------------------------------------------
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
    """Velg en tilfeldig fiendeklasse basert på progression level."""
    pool = ENEMY_POOL.get(min(progression_level, 10), ENEMY_POOL[10])
    return random.choice(pool)

def scale_enemy(enemy, progression_level: int):
    """
    Skalerer en fiends stats basert på progression level.

    HP skalerer raskere enn skade slik at rom føles tøffere
    uten at spilleren plutselig one-shottes.

    Scaling-kurve (eksempel):
      Level 1:  1.00x HP, 1.00x skade  (grunnlinje)
      Level 5:  1.60x HP, 1.32x skade
      Level 10: 2.35x HP, 1.72x skade

    Vil du ha raskere scaling? Øk 0.15 (HP) og 0.08 (skade).
    """
    if progression_level <= 1:
        return

    if hasattr(enemy, 'is_boss'):
        return
    hp_mult = 1.0 + (progression_level - 1) * 0.15
    dmg_mult = 1.0 + (progression_level - 1) * 0.08

    enemy.health = int(enemy.health * hp_mult)
    if hasattr(enemy, 'gun'):
        enemy.gun.damage = round(enemy.gun.damage * dmg_mult, 1)
    else:
        enemy.damage = round(enemy.damage * dmg_mult, 1)