import pygame

from .enemy import Enemy

# ===========================================================================
# ELITE FIENDER — elite_enemies.py
# ===========================================================================
#
# Elitefiender er sterkere varianter med spesialmekanikker.
# De introduseres gradvis gjennom progression-systemet (se progression.py).
#
# --- Oversikt ---
# ScoutEnemy      : Vet alltid hvor du er, så ingen detection radius
# AssassinEnemy   : Rask melee + lunge-angrep med windup
# SlowEnemy       : Treig men slår hardt, windup-angrep
# BruteEnemy      : Stor, høy damage og lang rekkevidde
# TankEnemy       : Mest helse, også mye damage
#
# --- Stat-referanse ---
# 1 tile = 96px | Spillerens hastighet = ~430 px/s
# ===========================================================================

class ScoutEnemy(Enemy):
    """
    Ingen detection_radius, er alltid i chase.
    """
    name               = "scout_enemy"
    speed              = 330
    health             = 55
    damage             = 10
    attack_range       = 4225
    attack_cooldown    = 900
    knockback_strength = 8
    color              = (60, 210, 220)
    xp_reward          = 18
    width              = 38
    height             = 38
    knockback_friction = 0.75

    def __init__(self, x, y):
        super().__init__(x, y)

    def move(self, player, obstacles, room, dt_ms):
        now = pygame.time.get_ticks()

        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            self.wander_goal_g = None
            return

        if self.hit:
            self.hit = False

        player_center = player.rect.center

        self.update_knockback(obstacles)
        self._move_towards(player_center, obstacles, dt_ms)

        if now >= self.attack_cooldown_until and self.rect.colliderect(player.rect):
            self._damage_player(player, self.damage)
            self.attack_cooldown_until = now + self.attack_cooldown
            self.apply_knockback(player.rect, 4)


class AssassinEnemy(Enemy):
    """
    Har et eget lunge angrep.
    """
    name              = "assassin_enemy"
    speed             = 400
    health            = 65
    damage            = 35
    detection_radius  = 900
    attack_range      = 4900    # 70 px
    attack_cooldown   = 1100
    knockback_strength= 24
    color             = (200, 30, 60)    # crimson
    xp_reward         = 28
    width             = 34
    height            = 34
    wander_radius     = 4
    knockback_friction= 0.75
    _LUNGE_MAX_DIST   = 500
    _LUNGE_SPEED      = 650
    _LUNGE_AREA       = 330000
    _LUNGE_COOLDOWN   = 3000

    def __init__(self, x, y):
        super().__init__(x, y)
        self.lunge_hit = False
        self._lunge_windup = 600
        self._lunge_windup_until = 0
        self.state = "chase"
        self._lunge_direction = pygame.Vector2()
        self._lunge_start = pygame.Vector2()
        self._lunge_cooldown_until = 0

    def move(self, player, obstacles, room, dt_ms):
        now = pygame.time.get_ticks()

        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            self.wander_goal_g = None
            return

        if self.hit and self.state not in ("lunge", "lunge_windup", "attack"):
            self.hit = False
            self.last_seen_pos = player.rect.center
            self.search_started = now
            self.state = "search"

        player_center = player.rect.center
        enemy_center = self.rect.center
        see_player = False

        dist2_to_player = self._dist2(*player_center, *enemy_center)
        if dist2_to_player <= self.detection_radius * self.detection_radius:
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):
                see_player = True
                self.last_seen_pos = player_center
                self.search_started = None

        self.update_knockback(obstacles)

        if self.state in ("idle", "walk"):
            if see_player:
                self.state = "chase"
            else:
                self._idle(room, obstacles, dt_ms, now)

        elif self.state == "chase":
            self.wander_goal_g = None
            if see_player:
                self._move_towards(player_center, obstacles, dt_ms)
                if now >= self.attack_cooldown_until and self.rect.colliderect(player.rect):
                    self._damage_player(player, self.damage)
                    self.attack_cooldown_until = now + self.attack_cooldown
                    self.apply_knockback(player.rect, 4)
                elif dist2_to_player <= self._LUNGE_AREA and self._lunge_cooldown_until < now:
                    self.state = "lunge_windup"
                    self._lunge_windup_until = now + self._lunge_windup
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"

        elif self.state == "lunge_windup":
            if now > self._lunge_windup_until:
                self._lunge_direction = (player.pos - self.pos).normalize()
                self._lunge_start = pygame.Vector2(self.pos)
                self.state = "lunge"

        elif self.state == "lunge":
            if (self.pos - self._lunge_start).length() > self._LUNGE_MAX_DIST:
                self.state = "chase"
                self._lunge_cooldown_until = now + self._LUNGE_COOLDOWN
                self.lunge_hit = False
            else:
                hit = self._lunge(self._lunge_direction.x * self._LUNGE_SPEED,
                                  self._lunge_direction.y * self._LUNGE_SPEED, dt_ms, obstacles)
                if hit:
                    self.state = "chase"
                    self._lunge_cooldown_until = now + self._LUNGE_COOLDOWN
                    self.lunge_hit = False
                if self.rect.colliderect(player.rect) and not self.lunge_hit:
                    self._damage_player(player, self.damage)
                    self.lunge_hit = True

        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now)
            else:
                self.state = "idle"

        elif self.state == "dead":
            return


# ===========================================================================
# WINDUP MELEE MIXIN
# ===========================================================================
# SlowEnemy, BruteEnemy og TankEnemy bruker alle windup-angrep:
# Fienden stopper opp, venter (attack_windup_ms), og slår deretter.
# Spilleren har tid til å dodge i vinduptiden..
# ===========================================================================


class WindupMeleeMixin:
    """Felles move()-logikk for fiender med windup-angrep."""

    def move(self, player, obstacles, room, dt_ms):
        now = pygame.time.get_ticks()

        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            self.wander_goal_g = None
            return

        if self.hit and self.state not in ("attack", "chase"):
            self.hit = False
            self.last_seen_pos = player.rect.center
            self.search_started = now
            self.state = "search"

        player_center = player.rect.center
        enemy_center = self.rect.center
        see_player = False
        dist2_to_player = self._dist2(*player_center, *enemy_center)

        if dist2_to_player <= self.detection_radius * self.detection_radius:
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):
                see_player = True
                self.last_seen_pos = player_center
                self.search_started = None

        self.update_knockback(obstacles)

        if self.state in ("idle", "walk"):
            if see_player:
                self.state = "chase"
            else:
                self._idle(room, obstacles, dt_ms, now)

        elif self.state == "chase":
            self.wander_goal_g = None
            if see_player:
                if now >= self.attack_cooldown_until and dist2_to_player <= self.attack_range:
                    self.state = "attack"
                    self.attack_windup_until = now + self.attack_windup_ms
                else:
                    self._move_towards(player_center, obstacles, dt_ms)
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"

        elif self.state == "attack":
            if now >= self.attack_windup_until:
                if dist2_to_player <= self.attack_range:
                    self._damage_player(player, self.damage)
                self.state = "chase"
                self.attack_cooldown_until = now + self.attack_cooldown

        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now)
            else:
                self.state = "idle"

        elif self.state == "dead":
            return

class SlowEnemy(WindupMeleeMixin, Enemy):
    """
    Sier seg vel selv.
    """
    name              = "slow_enemy"
    speed             = 280
    health            = 90
    damage            = 26
    detection_radius  = 700
    attack_range      = 6500    # 75 px
    attack_cooldown   = 1300
    attack_windup_ms  = 300
    knockback_strength= 22
    color             = (140, 60, 200)   # dark purple
    xp_reward         = 22
    width             = 52
    height            = 52
    wander_radius     = 2
    knockback_friction= 0.6

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0

class BruteEnemy(WindupMeleeMixin, Enemy):
    """
    Mer skade enn slow og tank.
    """
    name              = "brute_enemy"
    speed             = 330
    health            = 160
    damage            = 34
    detection_radius  = 800
    attack_range      = 6400    # 80 px
    attack_cooldown   = 1500
    attack_windup_ms  = 500
    knockback_strength= 28
    color             = (200, 100, 40)   # dark orange-brown
    xp_reward         = 45
    width             = 58
    height            = 58
    wander_radius     = 3
    knockback_friction= 0.5

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0

class TankEnemy(WindupMeleeMixin, Enemy):
    """
    Høy helse, høy skade. Tank. 
    """
    name              = "tank_enemy"
    speed             = 310
    health            = 300
    damage            = 28
    detection_radius  = 700
    attack_range      = 7225    # 85 px
    attack_cooldown   = 1800
    attack_windup_ms  = 400
    knockback_strength= 32
    color             = (120, 140, 160)  # steel blue-grey
    xp_reward         = 60
    width             = 64
    height            = 64
    wander_radius     = 2
    knockback_friction= 0.4

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0