# colors
BLACK  = (0, 0, 0)
RED    = (255, 0, 0)
GREEN  = (0, 255, 0)
BLUE   = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 128, 0)
WHITE = (255, 255, 255)

PLAYER_COLOR = (255, 255, 255)

# gameplay – player
PLAYER_SPEED   = 5
PLAYER_DPS     = 1
PLAYER_HEALTH  = 5
PLAYER_SIZE    = (50, 50)
ALIVE          = True
PLAYER_ATTACK_COOLDOWN = 500
DASH_SPEED = 8          # Hvor fort man dasher (piksler per frame)
DASH_DURATION = 230      # Hvor lenge dashen varer (ms)
DASH_COOLDOWN = 1300     # Tid mellom hver dash (ms)
PLAYER_KNOCKBACK_STRENGTH = 12  # Piksler per frame ved treff
PLAYER_KNOCKBACK_FRICTION = 0.75  # Demping per frame (0–1)
PLAYER_HIT_INVINCIBLE_MS = 600  # Post-hit iframes (ms)

# gameplay - projectile
PROJECTILE_DAMAGE = 1
PROJECTILE_SPEED = 600

# gameplay – enemy
ENEMY_SPEED        = 140
ENEMY_DPS          = 1
ENEMY_HEALTH       = 3
DETECTION_RADIUS   = 550                  # px
LOSE_SIGHT_TIME    = 2400                 # ms i search før idle
ATTACK_RANGE       = 200                   # px (nærkamp)
ENEMY_SIZE         = (50, 50)
ENEMY_ATTACK_COOLDOWN    = 500            # ms
ENEMY_WANDER_INTERVAL_MS = (1200, 2500)   # (min, max) ms pause mellom impulser
ENEMY_WANDER_RADIUS_TILES = 3             # hvor langt fra nåværende grid-rute
ENEMY_ATTACK_WINDUP_MS = 400    # Standard windup-tid
ENEMY_KNOCKBACK_STRENGTH = 10   # Standard knockback-kraft


# gameplay - door
OPPOSITE = {"N":"S","S":"N","E":"W","W":"E"} # motsatt retning av der man kom inn

# buffs (varighets-tabell)
BUFF_DURATIONS = {
    'speed_boost':  5000,  # 5s
    'attack_boost': 7000,  # 7s
    'shield_boost': 10000, # 10s
}

# constants.py
TILE_SIZE = 64

# terrain tiles
TILE_FLOOR = 0
TILE_WALL  = 1

# debug
DEBUG_SHOW_HITBOXES = True
DEBUG_HITBOX_MS     = 120   # hvor lenge (ms) et angrep vises
HITBOX_COLOR_RGBA   = (255, 60, 0, 120)   # semi-transparent oransje/rød
HURTBOX_COLOR_RGBA  = (0, 200, 255, 80)   # semi-transparent cyan (om du vil vise hurtbox)

