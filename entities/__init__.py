from .player import Player
from .door import Door
from .entity import Entity
from .enemies import Enemy, FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy, AssassinEnemy, BruteEnemy, SwarmEnemy, BossEnemy

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
    "BossEnemy":     BossEnemy
}