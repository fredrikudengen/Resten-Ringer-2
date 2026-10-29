import math
import random

import pygame

from src.core import constants, debug
from src.entities.entity import Entity
from src.entities.enemies.pathfinding import PathfindingMixin
from src.entities.enemies.movement import MovementMixin


class Enemy(PathfindingMixin, MovementMixin, Entity):

    detection_radius = 0  # px; None = alltid oppdaget (se ScoutEnemy)
    flinch_ms        = constants.ENEMY_FLINCH_MS
    knockback_taken_mult = 1.0  # ganges med våpenets knockback_strength; lav = tung/vanskelig å dytte
    contact_self_knockback = 16  # fienden dyttes litt tilbake når den treffer spilleren
    reaction_ms      = constants.ENEMY_REACTION_MS
    stat_spread      = constants.ENEMY_STAT_SPREAD

    def __init__(self, x, y):

        super().__init__(x, y)

        self.max_health = self.health

        now = pygame.time.get_ticks()

        # Variasjon per fiende (#23), så en gruppe ikke beveger seg som én klump
        self._randomize_stats()
        self._spotted_at         = None

        self.alive                 = True
        self.hit                   = False
        self.attack_cooldown_until = 0

        self.state          = "idle"
        self.last_seen_pos  = None
        self.search_started = None
        self._debug_los     = None

        self.wander_goal_g       = None
        self.wander_end          = False
        self.next_wander_at      = now + random.randint(1200, 2500)
        self.WANDER_INTERVAL_MS  = (1500, 2500)
        self.wander_radius       = 4

        self.facing_left         = False

        self.velocity            = pygame.math.Vector2(0, 0)  # px/s, styres via _steer()
        self._steered            = False

        # Retningsstøy (#21): egen klokke og fase per fiende så de ikke svinger i takt
        self._noise_t            = 0.0
        self._noise_phase        = (random.uniform(0, 2 * math.pi), random.uniform(0, 2 * math.pi))

        self._init_burst()

        # Treff-reaksjon (#25)
        self.flinch_until        = 0
        self.hurt_until          = 0
        self._flinch_ready_at    = 0

    def _randomize_stats(self):
        """Gi fienden ±stat_spread tilfeldig fart, reaksjonstid og aggressivitet.

        Aggressivitet > 1 betyr kortere attack_cooldown og større detection_radius.
        Settes som instans-attributter, så klasseverdiene er uendret.
        """
        s = self.stat_spread
        if s <= 0:
            self.aggression = 1.0
            return

        self.speed       = self.speed * random.uniform(1 - s, 1 + s)
        self.reaction_ms = self.reaction_ms * random.uniform(1 - s, 1 + s)
        self.aggression  = random.uniform(1 - s, 1 + s)

        if hasattr(self, "attack_cooldown"):
            self.attack_cooldown = self.attack_cooldown / self.aggression
        if self.detection_radius:
            self.detection_radius = self.detection_radius * self.aggression

    def _reacted(self, see_player, now) -> bool:
        """True når fienden har sett spilleren sammenhengende i reaction_ms."""
        if not see_player:
            self._spotted_at = None
            return False
        if self._spotted_at is None:
            self._spotted_at = now
        if now - self._spotted_at < self.reaction_ms:
            return False
        self._spotted_at = None
        return True

    # ------------------------- PUBLIC API -------------------------

    def on_hit(self, source_rect, knockback_strength):
        """Reaksjon når fienden treffes: knockback, kort stopp (flinch) og hurt-visuell.

        Hurt-visuellen (tint + "hurt"-frame) vises i flinch_ms ved hvert treff. Selve
        stoppet har cooldown, så raske våpen ikke stunlocker fienden.
        """
        now = pygame.time.get_ticks()
        self.hit = True
        self.apply_knockback(source_rect, knockback_strength * self.knockback_taken_mult)
        hurt_ms = self.flinch_ms if self.flinch_ms > 0 else constants.ENEMY_HURT_FLASH_MS
        self.hurt_until = now + hurt_ms

        if self.flinch_ms > 0 and now >= self._flinch_ready_at:
            self.flinch_until = now + self.flinch_ms
            self._flinch_ready_at = self.flinch_until + constants.ENEMY_FLINCH_COOLDOWN_MS
            self.velocity.update(0, 0)  # stopp opp, så knockbacken faktisk synes

    def _flinching(self) -> bool:
        return pygame.time.get_ticks() < self.flinch_until

    def _hurt(self) -> bool:
        return pygame.time.get_ticks() < self.hurt_until

    def _hurt_visual(self, frame: str) -> tuple[str, tuple[int, int, int] | None]:
        """(frame, tint) for tegning: tint + "hurt"-frame (hvis spriten har en) mens fienden er truffet."""
        if not self._hurt():
            return frame, None
        hurt_frame = "hurt" if self.sprite.has_frame("hurt") else frame
        return hurt_frame, constants.ENEMY_HURT_TINT

    def move(self, player, obstacles, room, dt_ms):
        """
        Oppdater fienden én frame: sansing, state-maskin, bevegelse.

        Args:
            player: objekt med .rect (pygame.Rect)
            obstacles: iterable av vegg-rektangler for kollisjon
            room: GridRoom med is_blocked(...) og TILE_SIZE
            dt_ms: millisekunder siden forrige frame
        """
        now = pygame.time.get_ticks()

        if self.health <= 0:
            self.alive         = False
            self.state         = "dead"
            self.wander_goal_g = None
            return

        if self.hit and self.state not in ("attack", "chase"):
            self.hit            = False
            self.last_seen_pos  = player.rect.center
            self.search_started = now
            self.state          = "search"

        player_center = player.rect.center
        enemy_center  = self.rect.center
        see_player    = False
        
        self._debug_los = None
        dist2_to_player = self._dist2(*player_center, *enemy_center)
        if dist2_to_player <= self.detection_radius * self.detection_radius:
            self._debug_los = player_center
            if self._has_los(room, *self._grid_pos(), *player._grid_pos()):
                see_player          = True
                self.last_seen_pos  = player_center
                self.search_started = None

        self.update_knockback(obstacles)

        if self.state in ("idle", "walk"):
            if self._reacted(see_player, now):
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
                    self.apply_knockback(player.rect, self.contact_self_knockback)
            else:
                if self.last_seen_pos:
                    self.state = "search"
                    self.search_started = now
                else:
                    self.state = "idle"

        elif self.state == "search":
            if see_player:
                self.state = "chase"
            elif self.last_seen_pos:
                self._search(obstacles, room, dt_ms, now) 
            else:
                self.state = "idle"

        elif self.state == "dead":
            return

        self._update_facing()

    def _update_facing(self):
        """Snu spriten etter fiendens egen bevegelse (velocity), ikke posisjonsendring.

        Knockback flytter pos uten å endre velocity, så fienden snur seg ikke når den treffes.
        Liten dødsone så den ikke flimrer når farten er nesten null.
        """
        if abs(self.velocity.x) > 5.0:
            self.facing_left = self.velocity.x < 0

    def _sprite_frame(self) -> str:
        return "idle"

    def _is_moving(self) -> bool:
        if self._burst_paused() or self._flinching():
            return False
        return self.state == "chase" or self.state == "search" or (
            self.state == "idle" and self.wander_goal_g is not None
        )

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        # if self.state == "idle":
        #     color = self.color
        # elif self.state == "chase":
        #     color = tuple(min(c + 40, 255) for c in self.color)
        # elif self.state == "search":
        #     color = tuple(max(c - 40, 0) for c in self.color)
        # elif self.state == "attack":
        #     color = (255, 255, 255)
        # elif self.state == "dead":
        #     color = (100, 100, 100)
        # else:
        #     color = self.color

        frame, tint = self._hurt_visual(self._sprite_frame())
        self.sprite.draw(
            screen, draw_rect, frame=frame, tint=tint,
            flip_x=self.facing_left, moving=self._is_moving(),
            gait_phase=self._gait_phase(),
        )
        self._draw_healthbar(screen, camera)

        if self.state in ("idle", "walk") and self.wander_goal_g is not None:
            debug.draw_tile(screen, camera, self.wander_goal_g)

        if self._debug_los is not None:
            debug.draw_line(screen, camera, self.rect.center, self._debug_los)

        if self.detection_radius is not None:
            debug.draw_circle(screen, camera, self.rect.center, self.detection_radius)
        debug.draw_label(screen, camera, (self.rect.centerx, self.rect.top - 20), self.state)

    def _draw_healthbar(self, screen, camera):
        """Liten helsebar over fienden. Skjult ved full helse."""
        if not self.alive or self.health <= 0 or self.health >= self.max_health:
            return

        ratio = max(0.0, min(1.0, self.health / self.max_health))

        draw_rect = camera.apply(self.rect)
        border = 2
        bar_w  = draw_rect.width
        bar_h  = 8
        bar_x  = draw_rect.x
        bar_y  = draw_rect.top - bar_h - 8

        outer = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        inner = outer.inflate(-border * 2, -border * 2)

        filled_w  = int(inner.width * ratio)
        red_rect  = pygame.Rect(inner.x, inner.y, filled_w, inner.height)
        grey_rect = pygame.Rect(inner.x + filled_w, inner.y, inner.width - filled_w, inner.height)

        if red_rect.width > 0:
            pygame.draw.rect(screen, (200, 40, 40), red_rect)
        if grey_rect.width > 0:
            pygame.draw.rect(screen, (110, 110, 110), grey_rect)
        pygame.draw.rect(screen, (255, 255, 255), outer, border)

    # ---------- HELPERS ----------
        
    def _idle(self, room, obstacles, dt_ms, now):
        """Håndter idle state med micro-wander."""
        if self.wander_goal_g is not None:
            waypoint_g = self._micro_wander(room, self.wander_goal_g, self.wander_radius)
            if waypoint_g:
                target_px = self._center_of_tile(*waypoint_g)
                reached = self._move_towards(target_px, obstacles, dt_ms)
                wander_end = reached and waypoint_g == self.wander_goal_g  # mellompunkt avslutter ikke turen
            else:
                wander_end = True  

            gx, gy = self._grid_pos()
                    
            if wander_end or (gx, gy) == self.wander_goal_g:
                self.wander_goal_g = None
                wait = random.randint(*self.WANDER_INTERVAL_MS)
                self.next_wander_at = now + wait
                        
        elif now >= self.next_wander_at:
            start_g = self._grid_pos()
            goal = self._pick_random_free_tile(room, start_g, self.wander_radius)
            if goal and goal != start_g:
                self.wander_goal_g = goal
            else:
                wait = random.randint(*self.WANDER_INTERVAL_MS)
                self.next_wander_at = now + wait
    
    def _search(self, obstacles, room, dt_ms, now):
        """Håndter search state. Gå mot siste kjente posisjon."""
        T = constants.TILE_SIZE
        goal_g = (self.last_seen_pos[0] // T, self.last_seen_pos[1] // T)
        waypoint_g = self._smoothed_next_waypoint(room, goal_g, max_expansions=512)
        if waypoint_g and waypoint_g != goal_g:
            target_px = self._center_of_tile(*waypoint_g)
            self._move_towards(target_px, obstacles, dt_ms)
            reached = False  # et mellompunkt på stien avslutter ikke søket
        else:
            # Fri sikt til målet (eller ingen sti) – gå rett mot siste kjente posisjon
            reached = self._move_towards(self.last_seen_pos, obstacles, dt_ms)

        timedout = self.search_started and (now - self.search_started > constants.LOSE_SIGHT_TIME)
        if reached or timedout:
            self.state = "idle"
            self.last_seen_pos = None
            self.search_started = None  

    def _damage_player(self, player, amount):

        if player.is_invincible:
            return

        player.health -= int(amount)

        for relic in player.relics:
            relic.on_hit(player)

        player.apply_knockback(self.rect, self.knockback_strength)

        # iframes
        player.hurt_invincible_until = pygame.time.get_ticks() + constants.PLAYER_HIT_INVINCIBLE_MS

        if player.health <= 0:
            player.alive = False

    def _pick_random_free_tile(self, room, center_g, radius):
        """
        Velg en tilfeldig fri tile.

        Args:
            center_g: grid posisjon start
            radius: radius i tiles
        """
        tries = 7
        cx, cy = center_g
        for _ in range(tries):
            nx = cx + random.randint(-radius, radius)
            ny = cy + random.randint(-radius, radius)
            if not room.is_blocked(nx, ny):
                return (nx, ny)
        return None