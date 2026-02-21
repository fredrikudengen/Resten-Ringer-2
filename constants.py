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

# gameplay - projectile
PROJECTILE_DAMAGE = 1
PROJECTILE_SPEED  = 600

# gameplay – enemy
LOSE_SIGHT_TIME          = 2400                 # ms i search før idle
ENEMY_WANDER_INTERVAL_MS = (1200, 2500)   # (min, max) pause 

# XP og level
XP_BASE               = 100     # XP til level 2
XP_SCALE              = 1.5     # Skalering per level (100 → 150 → 225 …)
XP_HP_BONUS_PER_LEVEL = 5       # Ekstra max-HP per level

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
TILE_FLOOR = 0
TILE_WALL  = 1

