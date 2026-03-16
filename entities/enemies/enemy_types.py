from .enemy import Enemy


# ---------------------------------------------------------------------------
# Stat reference
# ---------------------------------------------------------------------------
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
    speed             = 140
    health            = 25
    damage            = 8
    detection_radius  = 450
    attack_range      = 3600    # 60 px
    attack_cooldown   = 500
    attack_windup_ms  = 180
    knockback_strength= 6
    color             = (120, 220, 80)   # lime-green
    xp_reward         = 8
    width             = 28
    height            = 28
    wander_radius     = 6

    def __init__(self, x, y):
        super().__init__(x, y)


class FastEnemy(Enemy):
    """
    Quick and nimble; closes distance before you can react.
    Medium damage, short telegraph. ~2 shots to kill.
    """
    speed             = 165
    health            = 45
    damage            = 12
    detection_radius  = 650
    attack_range      = 4225    # 65 px
    attack_cooldown   = 650
    attack_windup_ms  = 300
    knockback_strength= 10
    color             = (255, 120, 30)   # bright orange
    xp_reward         = 15
    width             = 36
    height            = 36
    wander_radius     = 5

    def __init__(self, x, y):
        super().__init__(x, y)


class SlowEnemy(Enemy):
    """
    Lumbering but hits brutally hard.
    Long telegraph — punishes players who don't dash away. ~4 shots.
    """
    speed             = 55
    health            = 80
    damage            = 28
    detection_radius  = 550
    attack_range      = 5625    # 75 px
    attack_cooldown   = 1300
    attack_windup_ms  = 900
    knockback_strength= 22
    color             = (140, 60, 200)   # dark purple
    xp_reward         = 22
    width             = 52
    height            = 52
    wander_radius     = 2

    def __init__(self, x, y):
        super().__init__(x, y)


class ScoutEnemy(Enemy):
    """
    Enormous detection radius — spots you across the room.
    Weak in a fight but will always find you first. ~3 shots.
    """
    speed             = 115
    health            = 55
    damage            = 10
    detection_radius  = 1100    # biggest in the game
    attack_range      = 4225    # 65 px
    attack_cooldown   = 900
    attack_windup_ms  = 550
    knockback_strength= 8
    color             = (60, 210, 220)   # cyan
    xp_reward         = 18
    width             = 38
    height            = 38
    wander_radius     = 5

    def __init__(self, x, y):
        super().__init__(x, y)


class AssassinEnemy(Enemy):
    """
    Deceptively fast with devastating burst damage.
    Medium telegraph; rewards players who read the timing. ~3 shots.
    """
    speed             = 155
    health            = 65
    damage            = 35
    detection_radius  = 750
    attack_range      = 4900    # 70 px
    attack_cooldown   = 1100
    attack_windup_ms  = 400
    knockback_strength= 18
    color             = (200, 30, 60)    # crimson
    xp_reward         = 28
    width             = 34
    height            = 34
    wander_radius     = 4

    def __init__(self, x, y):
        super().__init__(x, y)


class BruteEnemy(Enemy):
    """
    Slow, massive, and extremely tough.
    Very long telegraph but massive damage and knockback. ~9 shots.
    """
    speed             = 70
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

    def __init__(self, x, y):
        super().__init__(x, y)


class TankEnemy(Enemy):
    """
    Armoured behemoth — almost unkillable without sustained focus.
    Moderate damage but incredible hp and reach. ~15 shots.
    """
    speed             = 40
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

    def __init__(self, x, y):
        super().__init__(x, y)


class BossEnemy(Enemy):
    """
    The apex threat. Fast for its size, enormous health pool,
    crushing damage. The long windup is your only window. ~25 shots.
    """
    speed             = 90
    health            = 500
    damage            = 50
    detection_radius  = 850
    attack_range      = 10000   # 100 px
    attack_cooldown   = 2200
    attack_windup_ms  = 1600
    knockback_strength= 45
    color             = (255, 200, 30)   # gold
    xp_reward         = 150
    width             = 78
    height            = 78
    wander_radius     = 4

    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, screen, camera):
        """Custom draw: gold body + bright border to signal 'elite threat'."""
        import pygame
        super().draw(screen, camera)
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 120), draw_rect, 3)