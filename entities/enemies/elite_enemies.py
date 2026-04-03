import pygame

from .enemy import Enemy


class AssassinEnemy(Enemy):
    """
    Deceptively fast with devastating burst damage.
    Medium telegraph; rewards players who read the timing. ~3 shots.
    """
    name              = "assassin_enemy"
    speed             = 230
    health            = 65
    damage            = 35
    detection_radius  = 750
    attack_range      = 4900    # 70 px
    attack_cooldown   = 1100
    attack_windup_ms  = 400
    knockback_strength= 24
    color             = (200, 30, 60)    # crimson
    xp_reward         = 28
    width             = 34
    height            = 34
    wander_radius     = 4
    knockback_friction= 0.75
    _LUNGE_MAX_DIST   = 500
    _LUNGE_SPEED      = 500
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
                if now >= self.attack_cooldown_until and dist2_to_player <= self.attack_range:
                    self.state = "attack"
                    self.attack_windup_until = now + self.attack_windup_ms
                    self._move_towards(player_center, obstacles, dt_ms)
                else:
                    self._move_towards(player_center, obstacles, dt_ms)
                    if dist2_to_player <= self._LUNGE_AREA and self._lunge_cooldown_until < now:
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