import random

import pygame

from .enemy import Enemy
from .ranged_enemy import RangedEnemy
from components.gun import EnemyPistol, EnemyRifle


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
        super().draw(screen, camera)
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 120), draw_rect, 3)


# ---------------------------------------------------------------------------
# Ranged enemies
# ---------------------------------------------------------------------------

class ShooterEnemy(RangedEnemy):
    """
    Standard ranged enemy. Keeps its distance and peppers the player
    with pistol fire. Repositions when LOS is broken.
    Fragile — punish it before it can reload. ~4 shots to kill.
    """
    gun_class          = EnemyPistol
    preferred_range_px = 300
    min_range_px       = 130

    speed              = 105
    health             = 75
    detection_radius   = 750
    knockback_strength = 0       # ranged — no melee knockback
    color              = (180, 80, 220)   # violet
    xp_reward          = 35
    width              = 36
    height             = 36
    wander_radius      = 5

    def __init__(self, x, y):
        super().__init__(x, y)


class MarksmanEnemy(RangedEnemy):
    """
    Long-range threat equipped with a slow but punishing rifle.
    Prefers to stay far back and take precise shots.
    Tougher than ShooterEnemy — needs focus fire to bring down. ~6 shots.
    """
    gun_class          = EnemyRifle
    preferred_range_px = 460
    min_range_px       = 200
    reposition_interval = 600   # repositions faster to keep sightlines open

    speed              = 80
    health             = 120
    detection_radius   = 900
    knockback_strength = 0
    color              = (220, 60, 60)   # deep red
    xp_reward          = 55
    width              = 40
    height             = 40
    wander_radius      = 4

    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, screen, camera):
        """Draw with a subtle border to telegraph elite ranged threat."""
        super().draw(screen, camera)
        if self.state not in ("dead", "reload"):
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, (255, 120, 120), draw_rect, 2)


# ---------------------------------------------------------------------------
# Boss enemy
# ---------------------------------------------------------------------------

class WardenBoss(Enemy):
    """
    The Warden — a slow, commanding boss that spawns minions.

    Phase 1 (100-50% HP):
      - Slow melee with long windup
      - Spawns 2-3 SwarmEnemies every 8 seconds (cap: 6 minions)

    Phase 2 (< 50% HP):
      - Speed increases noticeably
      - Spawn interval drops to 5s; spawns FastEnemies instead
      - Body pulses red to telegraph the phase shift
    """

    speed = 70
    health = 800
    damage = 55
    detection_radius = 900
    attack_range = 12100  # 110 px
    attack_cooldown = 2000
    attack_windup_ms = 1800
    knockback_strength = 50
    color = (255, 180, 20)  # deep gold
    xp_reward = 300
    width = 88
    height = 88
    wander_radius = 3

    _PHASE1_SPAWN_INTERVAL = 8000
    _PHASE2_SPAWN_INTERVAL = 5000
    _MINION_CAP = 6

    def __init__(self, x, y):
        super().__init__(x, y)
        self._phase = 1
        self._next_spawn_at = pygame.time.get_ticks() + self._PHASE1_SPAWN_INTERVAL
        self._initial_health = self.health  # snapshot before scaling
        self.pending_spawns: list = []

    # ---- overrides ----

    def move(self, player, obstacles, room, dt_ms):
        self._update_phase()
        self._try_spawn(pygame.time.get_ticks())
        super().move(player, obstacles, room, dt_ms)

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        if self.state == "dead":
            body_color = (80, 80, 80)
        elif self.state == "hurt":
            body_color = (255, 255, 255)
        elif self._phase == 2:
            pulse = (pygame.time.get_ticks() // 200) % 2 == 0
            body_color = (255, 60, 20) if pulse else (255, 140, 20)
        else:
            body_color = self.color

        pygame.draw.rect(screen, body_color, draw_rect)
        pygame.draw.rect(screen, (255, 255, 120), draw_rect, 4)  # gold border
        self._draw_health_bar(screen, draw_rect)

    # ---- private ----

    def _update_phase(self):
        if self._phase == 1 and self.health <= self._initial_health * 0.5:
            self._phase = 2
            self.speed = 130

    def _try_spawn(self, now):
        if now < self._next_spawn_at:
            return

        live = len(self.pending_spawns)
        if live >= self._MINION_CAP:
            self._next_spawn_at = now + 1000
            return

        count = random.randint(2, 3)
        minion_cls = FastEnemy if self._phase == 2 else SwarmEnemy
        for _ in range(count):
            ox = random.randint(-120, 120)
            oy = random.randint(-120, 120)
            self.pending_spawns.append(
                (minion_cls, self.rect.centerx + ox, self.rect.centery + oy)
            )

        interval = self._PHASE2_SPAWN_INTERVAL if self._phase == 2 else self._PHASE1_SPAWN_INTERVAL
        self._next_spawn_at = now + interval

    def _draw_health_bar(self, screen, draw_rect):
        bar_w = draw_rect.width + 20
        bar_h = 8
        bar_x = draw_rect.x - 10
        bar_y = draw_rect.y - 16

        ratio = max(0.0, self.health / max(1, self._initial_health))
        fill_w = int(bar_w * ratio)
        hp_color = (220, 60, 60) if self._phase == 2 else (255, 180, 20)

        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h))
        if fill_w > 0:
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 1)