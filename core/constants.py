from entities import (
    Enemy, FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy, BossEnemy,
)
from components import Speed_Powerup, Attack_Powerup, Shield_Powerup


# colors
BLACK  = (0, 0, 0)
RED    = (255, 0, 0)
GREEN  = (0, 255, 0)
BLUE   = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 128, 0)
WHITE  = (255, 255, 255)

PLAYER_COLOR = (255, 255, 255)

# gameplay – player
PLAYER_SPEED              = 5
PLAYER_DPS                = 1
PLAYER_HEALTH             = 5
PLAYER_SIZE               = (50, 50)
ALIVE                     = True
PLAYER_ATTACK_COOLDOWN    = 500
DASH_SPEED                = 8          
DASH_DURATION             = 230
DASH_COOLDOWN             = 1300  
PLAYER_KNOCKBACK_FRICTION = 0.9  
PLAYER_HIT_INVINCIBLE_MS  = 600  
BUFF_VALUES = {
    'speed_boost':  ('speed',  3),
    'attack_boost': ('dps',    1),
    'shield_boost': ('health', 2),
}

# gameplay - projectile
PROJECTILE_DAMAGE = 1
PROJECTILE_SPEED  = 600

# gameplay – enemy
LOSE_SIGHT_TIME          = 2400                
ENEMY_WANDER_INTERVAL_MS = (1200, 2500)   # (min, max) pause 

# XP og level
XP_BASE               = 100     # XP til level 2
XP_SCALE              = 1.5     # Skalering per level (100 → 150 → 225 …)
XP_HP_BONUS_PER_LEVEL = 5       
XP_DPS_BONUS_PER_LEVEL = 2
XP_SPEED_BONUS_PER_LEVEL = 1

# gameplay - door
OPPOSITE = {"N":"S","S":"N","E":"W","W":"E"} 

# buffs (varighets-tabell)
BUFF_DURATIONS = {
    'speed_boost':  5000,  
    'attack_boost': 7000,  
    'shield_boost': 10000, 
}

# constants.py
TILE_SIZE = 64

# terrain tiles
TILE_FLOOR       = 0
TILE_FLOOR_COLOR = (25, 25, 25)

TILE_WALL       = 1
TILE_WALL_COLOR = (80, 80, 80)

# door
DOOR_WIDTH  = TILE_SIZE  
DOOR_HEIGHT = TILE_SIZE

COLOR_DOOR_CLOSED  = (150, 50,  50)
COLOR_DOOR_OPEN    = (50,  150, 50)
COLOR_DOOR_OUTLINE = (0,   0,   0)

# grid room
CHAR_TO_TILE: dict[str, int] = {
    '.': TILE_FLOOR,
    '#': TILE_WALL,
}

CHAR_TO_SPAWN: dict[str, str] = {
    'E': 'enemy',
    'F': 'fast_enemy',
    'L': 'slow_enemy',
    'T': 'tank_enemy',
    'K': 'scout_enemy',
    'A': 'assassin_enemy',
    'R': 'brute_enemy',
    'W': 'swarm_enemy',
    'B': 'boss_enemy',
    'S': 'speed_powerup',
    'C': 'attack_powerup',
    'H': 'shield_powerup',
    'D': 'door',
}

# room manager
_TAG_TO_ENEMY: dict[str, type[Enemy]] = {
    'fast_enemy':     FastEnemy,
    'slow_enemy':     SlowEnemy,
    'tank_enemy':     TankEnemy,
    'scout_enemy':    ScoutEnemy,
    'assassin_enemy': AssassinEnemy,
    'brute_enemy':    BruteEnemy,
    'swarm_enemy':    SwarmEnemy,
    'boss_enemy':     BossEnemy,
}

_TAG_TO_POWERUP: dict[str, tuple[type, int]] = {
    'speed_powerup':  (Speed_Powerup,  20),
    'attack_powerup': (Attack_Powerup, 20),
    'shield_powerup': (Shield_Powerup, 20),
}

