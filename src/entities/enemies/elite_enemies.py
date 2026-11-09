import pygame

from src.core import constants
from src.view.sprite import Sprite
from src.view.afterimage import AfterimageTrail
from src.entities.enemies.enemy import Enemy

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
# SlowEnemy       : Treg men slår hardt, windup-angrep
# BruteEnemy      : Stor, høy damage, windup-slag + tung lunge
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
    accel_time_ms      = 150
    health             = 55
    damage             = 10
    attack_range       = 4225
    attack_cooldown    = 900
    knockback_strength = 8
    detection_radius   = None  # ser alltid spilleren, uansett avstand
    color              = (60, 210, 220)
    xp_reward          = 18
    width              = 96
    height             = 96
    knockback_friction = 0.75
    knockback_taken_mult = 0.8
    contact_self_knockback = 4

    def __init__(self, x, y):
        super().__init__(x, y)
        self.sprite = Sprite(
            frames={
                "idle": "enemy/scout/idle/idle",
                "walk": [f"enemy/scout/walk/{i}" for i in range(2)],
                "hurt": "enemy/scout/idle/idle",
            },
            base_size=(self.width, self.height),
            fallback_color=self.color,
            gait={"walk": {"cycle_ms": 400, "bounce": 14, "sway": 2, "lean": 3}},
        )

    def _react_to_hit(self, player, now):
        self.hit = False  # jager uansett, så et treff endrer ingenting

    def _sense(self, player, room) -> bool:
        return True  # vet alltid hvor spilleren er, uten siktlinje

    def _update_state(self, player, obstacles, room, dt_ms, now, see_player):
        """Ingen idle/search: scouten går alltid rett på spilleren langs korteste sti."""
        player_center = player.rect.center
        T = constants.TILE_SIZE
        goal_g = (player_center[0] // T, player_center[1] // T)
        waypoint_g = self._smoothed_next_waypoint(room, goal_g, max_expansions=512)
        if waypoint_g == goal_g:
            # Fri sikt til spillerens tile – gå rett mot spilleren, ikke tile-senteret
            self._move_towards(player_center, obstacles, dt_ms)
        elif waypoint_g:
            target_px = self._center_of_tile(*waypoint_g)
            self._move_towards(target_px, obstacles, dt_ms)
        else:
            self._move_towards(player_center, obstacles, dt_ms)

        self._contact_attack(player, now)

    def _sprite_frame(self) -> str:
        return "idle" if self.state == "dead" else "walk"

    def _is_moving(self) -> bool:
        return self.state != "dead" and not self._burst_paused() and not self._flinching()


# ===========================================================================
# LUNGE MIXIN
# ===========================================================================
# AssassinEnemy og BruteEnemy bruker lunge: fienden stopper (windup), kaster
# seg så i rett linje mot spilleren og skader alt den treffer på veien.
# Stopper ved vegg eller etter _LUNGE_MAX_DIST. Hver fiende har egen tuning.
# ===========================================================================

class LungeMixin:
    """Lunge-angrep oppå Enemy sin felles move() (med eller uten WindupMeleeMixin).

    Legges først i arvelisten. Tar over move() bare mens fienden er i
    "lunge_windup"/"lunge"; ellers kjører vanlig move() og lunge startes
    etterpå hvis fienden jager og spilleren er innenfor rekkevidde.
    """
    _LUNGE_WINDUP   = 600      # ms stillstand før hoppet (telegraph)
    _LUNGE_MAX_DIST = 500      # px før lungen avsluttes
    _LUNGE_SPEED    = 650      # px/s under lungen
    _LUNGE_AREA     = 330000   # maks avstand² for å starte lunge
    _LUNGE_MIN_AREA = 0        # min avstand², så nærkamp-fiender ikke lunger på kloss hold
    _LUNGE_COOLDOWN = 3000     # ms etter lungen før neste
    _LUNGE_DAMAGE_MULT = 1.0   # skade = damage * denne når lungen treffer

    def __init__(self, x, y):
        super().__init__(x, y)
        self._lunge_hit            = False  # lungen skader spilleren maks én gang
        self._lunge_windup_until   = 0
        self._lunge_direction      = pygame.Vector2()
        self._lunge_start          = pygame.Vector2()
        self._lunge_cooldown_until = 0
        self._lunge_trail          = AfterimageTrail()

    def draw(self, screen, camera):
        self._draw_lunge_trail(screen, camera)
        super().draw(screen, camera)

    def _draw_lunge_trail(self, screen, camera):
        """Etterbilder bak fienden mens den lunger. Tegnes før (under) selve spriten."""
        now = pygame.time.get_ticks()
        self._lunge_trail.update(self.state == "lunge", self.rect.center,
                                 self._visual_frame(), self.facing_left, now)
        self._lunge_trail.draw(screen, camera, self.sprite, (self.width, self.height), now)

    def move(self, player, obstacles, room, dt_ms):
        if self.health > 0 and self.state in ("lunge_windup", "lunge"):
            self.update_knockback(obstacles)
            self._update_lunge(player, obstacles, dt_ms, pygame.time.get_ticks())
            self._update_facing()
            return

        super().move(player, obstacles, room, dt_ms)
        self._try_start_lunge(player, room, pygame.time.get_ticks())

    def _try_start_lunge(self, player, room, now):
        if self.state != "chase" or now < self._lunge_cooldown_until:
            return
        dist2 = self._dist2(*player.rect.center, *self.rect.center)
        if not self._LUNGE_MIN_AREA <= dist2 <= self._LUNGE_AREA:
            return
        if not self._has_los(room, *self._grid_pos(), *player._grid_pos()):
            return
        self.state = "lunge_windup"
        self._lunge_windup_until = now + self._LUNGE_WINDUP

    def _update_lunge(self, player, obstacles, dt_ms, now):
        if self.state == "lunge_windup":
            if now > self._lunge_windup_until:
                self._begin_lunge(player)
            return

        if (self.pos - self._lunge_start).length() > self._LUNGE_MAX_DIST:
            self._end_lunge(now)
            return

        hit_wall = self._lunge(self._lunge_direction.x * self._LUNGE_SPEED,
                               self._lunge_direction.y * self._LUNGE_SPEED, dt_ms, obstacles)
        if self.rect.colliderect(player.rect) and not self._lunge_hit:
            self._damage_player(player, self.damage * self._LUNGE_DAMAGE_MULT)
            self._lunge_hit = True
        if hit_wall:
            self._end_lunge(now, hit_wall=True)

    def _begin_lunge(self, player):
        direction = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if direction.length_squared() < 1e-6:
            direction = pygame.Vector2(-1 if self.facing_left else 1, 0)
        self._lunge_direction = direction.normalize()
        self._lunge_start = pygame.Vector2(self.pos)
        self._lunge_hit = False
        self.state = "lunge"
        # Lunge nullstiller velocity, så retningen settes eksplisitt her
        if abs(self._lunge_direction.x) > 1e-3:
            self.facing_left = self._lunge_direction.x < 0

    def _end_lunge(self, now, hit_wall=False):
        """Lungen er over (nådde _LUNGE_MAX_DIST eller traff en vegg)."""
        self.state = "chase"
        self._lunge_cooldown_until = now + self._LUNGE_COOLDOWN
        self._lunge_hit = False


class AssassinEnemy(LungeMixin, Enemy):
    """
    Rask melee med lunge.
    """
    name              = "assassin_enemy"
    speed             = 400
    accel_time_ms     = 120
    health            = 65
    damage            = 35
    detection_radius  = 800
    attack_range      = 4900    # 70 px
    attack_cooldown   = 1100
    knockback_strength= 24
    color             = (200, 30, 60)    # crimson
    xp_reward         = 28
    width             = 80
    height            = 80
    wander_radius     = 4
    knockback_friction= 0.75
    knockback_taken_mult = 0.7
    contact_self_knockback = 4
    _LUNGE_WINDUP     = 600
    _LUNGE_MAX_DIST   = 500
    _LUNGE_SPEED      = 650
    _LUNGE_AREA       = 330000  # ~575 px
    _LUNGE_COOLDOWN   = 3000

    def __init__(self, x, y):
        super().__init__(x, y)
        self.state = "chase"
        self.sprite = Sprite(
            frames={
                "idle":   "enemy/assassin/enemy_assassin",
                "hurt":   "enemy/assassin/enemy_assassin",
                "windup": "enemy/assassin/enemy_assassin_windup",
                "lunge":  "enemy/assassin/enemy_assassin_lunge",
            },
            base_size=(self.width, self.height),
            fallback_color=self.color
        )

    def _sprite_frame(self) -> str:
        if self.state == "lunge_windup":
            return "windup"
        if self.state == "lunge":
            return "lunge"
        return "idle"


# ===========================================================================
# WINDUP MELEE MIXIN
# ===========================================================================
# SlowEnemy, BruteEnemy og TankEnemy bruker alle windup-angrep:
# Fienden stopper opp, venter (attack_windup_ms), og slår deretter.
# Spilleren har tid til å dodge i vinduptiden..
# ===========================================================================

class WindupMeleeMixin:
    """Windup-angrep: stopper i rekkevidde, lader opp (attack_windup_ms) og slår.

    Bruker Enemy sin felles tilstandsmaskin og fyller bare inn chase og "attack".
    """

    _STRIKE_MS    = 180   # ms "strike"-framen vises etter at slaget går av
    _strike_until = 0

    def _player_in_attack_range(self, player) -> bool:
        return self._dist2(*player.rect.center, *self.rect.center) <= self.attack_range

    def _chase(self, player, obstacles, room, dt_ms, now):
        if now >= self.attack_cooldown_until and self._player_in_attack_range(player):
            self.state = "attack"
            self.attack_windup_until = now + self.attack_windup_ms
        else:
            self._move_towards(player.rect.center, obstacles, dt_ms)

    def _update_special_state(self, player, obstacles, room, dt_ms, now, see_player):
        if self.state == "attack" and now >= self.attack_windup_until:
            if self._player_in_attack_range(player):
                self._damage_player(player, self.damage)
            self.state = "chase"
            self.attack_cooldown_until = now + self.attack_cooldown
            self._strike_until = now + self._STRIKE_MS

    def _sprite_frame(self) -> str:
        """windup mens slaget (eller lungen) lades, strike mens det treffer, ellers idle."""
        if self.state in ("attack", "lunge_windup"):
            return "windup"
        if self.state == "lunge" or pygame.time.get_ticks() < self._strike_until:
            return "strike"
        return "idle"

class SlowEnemy(WindupMeleeMixin, Enemy):
    """
    Sier seg vel selv.
    """
    name              = "slow_enemy"
    speed             = 280
    accel_time_ms     = 400
    health            = 90
    damage            = 26
    detection_radius  = 600
    attack_range      = 6500    # 75 px
    attack_cooldown   = 1300
    attack_windup_ms  = 300
    knockback_strength= 22
    color             = (140, 60, 200)   # dark purple
    xp_reward         = 22
    width             = 112
    height            = 112
    wander_radius     = 2
    knockback_friction= 0.6
    knockback_taken_mult = 0.7

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0
        self.sprite = Sprite(
            frames={
                "idle":   "enemy/slow/enemy_slow",
                "hurt":   "enemy/slow/enemy_slow",
                "windup": "enemy/slow/enemy_slow_windup",
                "strike": "enemy/slow/enemy_slow_strike",
            },
            base_size=(self.width, self.height),
            fallback_color=self.color
        )


class BruteEnemy(LungeMixin, WindupMeleeMixin, Enemy):
    """
    Mer skade enn slow og tank. Tung lunge: lengre windup og kortere hopp enn Assassin.
    """
    name              = "brute_enemy"
    speed             = 330
    accel_time_ms     = 450
    flinch_ms         = 80
    health            = 160
    damage            = 34
    detection_radius  = 700
    attack_range      = 6400    # 80 px
    attack_cooldown   = 1500
    attack_windup_ms  = 500
    knockback_strength= 28
    color             = (200, 100, 40)   # dark orange-brown
    xp_reward         = 45
    width             = 112
    height            = 112
    wander_radius     = 3
    knockback_friction= 0.5
    knockback_taken_mult = 0.6
    _LUNGE_WINDUP     = 750
    _LUNGE_MAX_DIST   = 320
    _LUNGE_SPEED      = 600
    _LUNGE_AREA       = 90000   # 300 px
    _LUNGE_MIN_AREA   = 25600   # 160 px – nærmere enn dette bruker den vanlig windup-slag
    _LUNGE_COOLDOWN   = 4500

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0
        self.sprite = Sprite(
            frames={
                "idle":   "enemy/brute/enemy_brute",
                "hurt":   "enemy/brute/enemy_brute",
                "windup": "enemy/brute/enemy_brute_windup",
                "strike": "enemy/brute/enemy_brute_strike",
            },
            base_size=(self.width, self.height),
            fallback_color=self.color
        )

class TankEnemy(WindupMeleeMixin, Enemy):
    """
    Høy helse, høy skade. Tank. 
    """
    name              = "tank_enemy"
    speed             = 310
    accel_time_ms     = 550
    flinch_ms         = 60
    health            = 300
    damage            = 28
    detection_radius  = 700
    attack_range      = 7225    # 85 px
    attack_cooldown   = 1800
    attack_windup_ms  = 400
    knockback_strength= 32
    color             = (120, 140, 160)  # steel blue-grey
    xp_reward         = 60
    width             = 128
    height            = 128
    wander_radius     = 2
    knockback_friction= 0.4
    knockback_taken_mult = 0.5

    def __init__(self, x, y):
        super().__init__(x, y)
        self.attack_windup_until = 0
        self.sprite = Sprite(
            frames={
                "idle":   "enemy/tank/enemy_tank",
                "hurt":   "enemy/tank/enemy_tank",
                "windup": "enemy/tank/enemy_tank_windup",
                "strike": "enemy/tank/enemy_tank_strike",
            },
            base_size=(self.width, self.height),
            fallback_color=self.color
        )