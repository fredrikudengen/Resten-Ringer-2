import pygame

from .enemy import Enemy
from .ranged_enemies import RangedEnemy
from components.gun import EnemyPistol, EnemyRifle

# ===========================================================================
# VANLIGE FIENDER — enemy_types.py
# ===========================================================================
#
# Her finner du de grunnleggende fiendene i spillet.
# Elitefiender (SlowEnemy, BruteEnemy, TankEnemy, ScoutEnemy, AssassinEnemy)
# ligger i elite_enemies.py
# Bosser ligger i boss_enemies.py
#
# --- Stat-referanse ---
# 1 tile = 96px
# Spillerens hastighet = ~430 px/s
# Pistol baseline: 20 skade/skudd, 350ms mellom skudd
#
# --- Nyttige verdier å justere ---
# speed            : px per sekund. Spilleren er ~430, så 400 = omtrent like rask
# health           : HP. Pistolskudd gjør 20 skade, så health=40 → 2 skudd
# damage           : Skade ved treff (melee) eller via gun (ranged)
# detection_radius : Pikselradius der fienden oppdager spilleren (krever siktlinje)
# attack_cooldown  : Millisekunder mellom angrep
# knockback_strength: Hvor langt spilleren kastes ved treff (høyere = lengre)
# knockback_friction: Hvor raskt knockback bremser (0.0 = stopper straks, 1.0 = glir evig)
# ===========================================================================


class SwarmEnemy(Enemy):
    """
    Liten og rask.
    """
    name              = "swarm_enemy"
    speed             = 400
    health            = 40
    damage            = 8
    detection_radius  = 1000
    attack_cooldown   = 500
    knockback_strength= 6
    color             = (120, 220, 80)   # lime-green
    xp_reward         = 8
    width             = 32
    height            = 32
    wander_radius     = 6
    knockback_friction= 0.95

    def __init__(self, x, y):
        super().__init__(x, y)


class FastEnemy(Enemy):
    """
    Raskeste fiende, litt mer liv enn swarm.
    """
    name              = "fast_enemy"
    speed             = 440
    health            = 45
    damage            = 12
    detection_radius  = 1000
    attack_cooldown   = 650
    knockback_strength= 10
    color             = (255, 120, 30)   # bright orange
    xp_reward         = 15
    width             = 40
    height            = 40
    wander_radius     = 5
    knockback_friction= 0.9

    def __init__(self, x, y):
        super().__init__(x, y)


# ===========================================================================
# RANGED FIENDER
# ===========================================================================
# Ranged fiender bruker gun-systemet i stedet for melee.
# De holder avstand og skyter mot spilleren.
#
# Viktige ranged-spesifikke verdier:
# preferred_range_px : Ideell avstand til spilleren mens de skyter
# min_range_px       : Vil aldri gå nærmere enn dette
# gun_class          : Hvilken pistol de bruker (se components/gun.py)
# ===========================================================================

class ShooterEnemy(RangedEnemy):
    """
    Sier seg selv egentlig.
    """
    name              = "shooter_enemy"
    gun_class          = EnemyPistol
    preferred_range_px = 300
    min_range_px       = 130

    speed              = 250
    health             = 75
    detection_radius   = 800
    knockback_strength = 0
    color              = (180, 80, 220)
    xp_reward          = 35
    width              = 36
    height             = 36
    wander_radius      = 5
    knockback_friction= 0.8

    def __init__(self, x, y):
        super().__init__(x, y)


class MarksmanEnemy(RangedEnemy):
    """
    Sniper. Lenger avstand, raskere skudd.
    """
    name              = "marksman_enemy"
    gun_class          = EnemyRifle
    preferred_range_px = 460
    min_range_px       = 200
    reposition_interval = 600

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
        super().draw(screen, camera)
        if self.state not in ("dead", "reload"):
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, (255, 120, 120), draw_rect, 2)
