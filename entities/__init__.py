from .player import Player
from .entity import Entity
from .enemies import (Enemy, FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy, AssassinEnemy, BruteEnemy,
                      SwarmEnemy, ShooterEnemy, MarksmanEnemy, WardenBoss)

__all__ = [
    # Base classes
    'Entity',
    'Player',
]

ENEMY_TYPES = {
    "Enemy":         Enemy,
    "FastEnemy":     FastEnemy,
    "SlowEnemy":     SlowEnemy,
    "TankEnemy":     TankEnemy,
    "ScoutEnemy":    ScoutEnemy,
    "AssassinEnemy": AssassinEnemy,
    "BruteEnemy":    BruteEnemy,
    "SwarmEnemy":    SwarmEnemy,
    "ShooterEnemy":  ShooterEnemy,
    "MarksmanEnemy": MarksmanEnemy,
    "WardenBoss":    WardenBoss
}
