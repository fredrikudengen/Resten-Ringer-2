import pygame

from .enemy import Enemy
from .ranged_enemies import RangedEnemy
from components.gun import EnemyPistol, EnemyRifle


# ---------------------------------------------------------------------------
# Stat reference
# ---------------------------------------------------------------------------
# Player speed = ~300
# Pistol baseline: 20 dmg/shot, 350 ms fire rate ≈ 57 DPS
# "shots" below = pistol shots to kill (hp / 20), rounded
# attack_range   = squared pixel radius (64 px melee = 4 096, 80 px = 6 400)
# ---------------------------------------------------------------------------

class SwarmEnemy(Enemy):
    """
    Individually fragile; lethal in packs.
    Tiny, fast, attacks rapidly with almost no telegraph.
    ~1 shot to kill — the danger is sheer numbers.
    """
    name              = "swarm_enemy"
    speed             = 280
    health            = 40
    damage            = 8
    detection_radius  = 1500
    attack_range      = 3600    # 60 px
    attack_cooldown   = 500
    attack_windup_ms  = 180
    knockback_strength= 6
    color             = (120, 220, 80)   # lime-green
    xp_reward         = 8
    width             = 28
    height            = 28
    wander_radius     = 6
    knockback_friction= 0.95

    def __init__(self, x, y):
        super().__init__(x, y)


class FastEnemy(Enemy):
    """
    Quick and nimble; closes distance before you can react.
    Medium damage, short telegraph. ~2 shots to kill.
    """
    name              = "fast_enemy"
    speed             = 310
    health            = 45
    damage            = 12
    detection_radius  = 1500
    attack_range      = 4225    # 65 px
    attack_cooldown   = 650
    attack_windup_ms  = 250
    knockback_strength= 10
    color             = (255, 120, 30)   # bright orange
    xp_reward         = 15
    width             = 36
    height            = 36
    wander_radius     = 5
    knockback_friction= 0.9

    def __init__(self, x, y):
        super().__init__(x, y)


class SlowEnemy(Enemy):
    """
    Lumbering but hits brutally hard.
    Long telegraph — punishes players who don't dash away. ~4 shots.
    """
    name              = "slow_enemy"
    speed             = 200
    health            = 80
    damage            = 28
    detection_radius  = 550
    attack_range      = 6500    # 75 px
    attack_cooldown   = 1300
    attack_windup_ms  = 600
    knockback_strength= 22
    color             = (140, 60, 200)   # dark purple
    xp_reward         = 22
    width             = 52
    height            = 52
    wander_radius     = 2
    knockback_friction= 0.6

    def __init__(self, x, y):
        super().__init__(x, y)


class ScoutEnemy(Enemy):
    """
    Enormous detection radius — spots you across the room.
    Weak in a fight but will always find you first. ~3 shots.
    """
    name              = "scout_enemy"
    speed             = 230
    health            = 55
    damage            = 10
    detection_radius  = 1200    # biggest in the game
    attack_range      = 4225    # 65 px
    attack_cooldown   = 900
    attack_windup_ms  = 550
    knockback_strength= 8
    color             = (60, 210, 220)   # cyan
    xp_reward         = 18
    width             = 38
    height            = 38
    wander_radius     = 5
    knockback_friction= 0.75

    def __init__(self, x, y):
        super().__init__(x, y)

class BruteEnemy(Enemy):
    """
    Slow, massive, and extremely tough.
    Very long telegraph but massive damage and knockback. ~9 shots.
    """
    name              = "brute_enemy"
    speed             = 180
    health            = 180
    damage            = 32
    detection_radius  = 520
    attack_range      = 6400    # 80 px
    attack_cooldown   = 1500
    attack_windup_ms  = 1000
    knockback_strength= 28
    color             = (200, 100, 40)   # dark orange-brown
    xp_reward         = 45
    width             = 58
    height            = 58
    wander_radius     = 3
    knockback_friction= 0.5

    def __init__(self, x, y):
        super().__init__(x, y)


class TankEnemy(Enemy):
    """
    Armoured behemoth — almost unkillable without sustained focus.
    Moderate damage but incredible hp and reach. ~15 shots.
    """
    name              = "tank_enemy"
    speed             = 170
    health            = 300
    damage            = 22
    detection_radius  = 480
    attack_range      = 7225    # 85 px
    attack_cooldown   = 1800
    attack_windup_ms  = 1300
    knockback_strength= 32
    color             = (120, 140, 160)  # steel blue-grey
    xp_reward         = 60
    width             = 64
    height            = 64
    wander_radius     = 2
    knockback_friction= 0.4

    def __init__(self, x, y):
        super().__init__(x, y)

# ---------------------------------------------------------------------------
# Ranged enemies
# ---------------------------------------------------------------------------

class ShooterEnemy(RangedEnemy):
    """
    Standard ranged enemy. Keeps its distance and peppers the player
    with pistol fire. Repositions when LOS is broken.
    Fragile — punish it before it can reload. ~4 shots to kill.
    """
    name              = "shooter_enemy"
    gun_class          = EnemyPistol
    preferred_range_px = 300
    min_range_px       = 130

    speed              = 250
    health             = 75
    detection_radius   = 750
    knockback_strength = 0       # ranged — no melee knockback
    color              = (180, 80, 220)   # violet
    xp_reward          = 35
    width              = 36
    height             = 36
    wander_radius      = 5
    knockback_friction= 0.8

    def __init__(self, x, y):
        super().__init__(x, y)


class MarksmanEnemy(RangedEnemy):
    """
    Long-range threat equipped with a slow but punishing rifle.
    Prefers to stay far back and take precise shots.
    Tougher than ShooterEnemy — needs focus fire to bring down. ~6 shots.
    """
    name              = "marksman_enemy"
    gun_class          = EnemyRifle
    preferred_range_px = 460
    min_range_px       = 200
    reposition_interval = 600   # repositions faster to keep sightlines open

    speed              = 240
    health             = 120
    detection_radius   = 900
    knockback_strength = 0
    color              = (220, 60, 60)   # deep red
    xp_reward          = 55
    width              = 40
    height             = 40
    wander_radius      = 4
    knockback_friction= 0.7

    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, screen, camera):
        """Draw with a subtle border to telegraph elite ranged threat."""
        super().draw(screen, camera)
        if self.state not in ("dead", "reload"):
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, (255, 120, 120), draw_rect, 2)
