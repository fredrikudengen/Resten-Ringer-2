import random

import pygame

from .enemy import Enemy
from .enemy_types import FastEnemy, SwarmEnemy
from .movement import MovementMixin

# ===========================================================================
# BOSSER — boss_enemies.py
# ===========================================================================
#
# Bosser er sluttutfordringen på hver etasje. De har egne faser,
# spesialangrep og visuell feedback.
#
# WardenBoss — "The Warden"
#   Fase 1 (100–50% HP): Sakte melee med lang windup + spawner SwarmEnemies
#   Fase 2 (< 50% HP):   Raskere, spawner FastEnemies, kortere spawn-intervall
#
# --- Verdier du kan justere for å endre boss-følelsen ---
# health              : Total HP (2000 er mye, så senk for raskere kamper)
# attack_windup_ms    : Telegraph-tid i ms (lengre = lettere å dodge)
# _LUNGE_SPEED        : Hastighet under lunge-angrep
# _PHASE1_SPAWN_INTERVAL: Sekunder mellom minion-spawns i fase 1
# _MINION_CAP         : Maks antall minions i fase 1
# _DAZE_DURATION_WALL : Hvor lenge bossen er svimmel etter å treffe en vegg
# ===========================================================================

class WardenBoss(Enemy, MovementMixin):
    """
    The Warden.
    """
    name = "warden_boss"
    speed = 100
    health = 2000
    damage = 55
    attack_range = 12100  # 110 px
    attack_cooldown = 2000
    attack_windup_ms = 1800
    knockback_strength = 50
    color = (255, 180, 20)  # deep gold
    xp_reward = 300
    width = 88
    height = 88
    is_boss = True

    _PHASE1_SPAWN_INTERVAL = 6000
    _PHASE2_SPAWN_INTERVAL = 5000
    _MINION_CAP = 6
    _MINION_CAP_PHASE2 = 9
    _LUNGE_SPEED = 700
    _LUNGE_MAX_DIST = 1200
    _PHASE1_LUNGE_COOLDOWN = 8000
    _PHASE2_LUNGE_COOLDOWN = 6000
    _DAZE_DURATION_WALL = 3000
    _DAZE_DURATION = 1500

    def __init__(self, x, y):
        super().__init__(x, y)
        self.state = "chase"
        self._lunge_windup_until = 0
        self._lunge_windup = 1500
        self.did_slam = False
        self._phase = 1
        self._next_spawn_at = pygame.time.get_ticks() + self._PHASE1_SPAWN_INTERVAL
        self._initial_health = self.health
        self.pending_spawns: list = []
        self._lunge_direction = pygame.Vector2()
        self._lunge_start = pygame.Vector2()
        self._lunge_cooldown_until = 0
        self._daze_until = 0

    def move(self, player, obstacles, room, dt_ms):
        now = pygame.time.get_ticks()

        self._update_phase()
        self._try_spawn(room, now)

        if self.health <= 0:
            self.alive = False
            self.state = "dead"
            return

        player_center = player.rect.center
        enemy_center = self.rect.center

        dist2_to_player = self._dist2(*player_center, *enemy_center)

        if self.state == "dazed":
            if self._daze_until < now:
                self._lunge_cooldown_until = now + self._PHASE1_LUNGE_COOLDOWN if self._phase == 1 \
                    else self._PHASE2_LUNGE_COOLDOWN
                self.state = "chase"
            else:
                return

        elif self.state == "chase":
            if now >= self.attack_cooldown_until and dist2_to_player <= (
                self.attack_range):
                    self.state = "attack"
                    self.attack_windup_until = now + self.attack_windup_ms
            else:
                self._move_towards(player_center, obstacles, dt_ms)
                if now > self._lunge_cooldown_until:
                    self.state = "lunge_windup"
                    self._lunge_windup_until = now + self._lunge_windup

        elif self.state == "lunge_windup":
            if now > self._lunge_windup_until:
                self._lunge_direction = (player.pos - self.pos).normalize()
                self._lunge_start = pygame.Vector2(self.pos)
                self.state = "lunge"

        elif self.state == "attack":
            if now >= self.attack_windup_until:
                if dist2_to_player <= self.attack_range:
                    self._damage_player(player, self.damage)
                self.state = "chase"
                self.attack_cooldown_until = now + self.attack_cooldown

        elif self.state == "lunge":
            if (self.pos - self._lunge_start).length() > self._LUNGE_MAX_DIST:
                self.did_slam = True
                self._daze_until = now + self._DAZE_DURATION
                self.state = "dazed"
            else:
                hit = self._lunge(self._lunge_direction.x * self._LUNGE_SPEED,
                                  self._lunge_direction.y * self._LUNGE_SPEED, dt_ms, obstacles)
                if hit:
                    self.did_slam = True
                    self._daze_until = pygame.time.get_ticks() + self._DAZE_DURATION_WALL
                    self.state = "dazed"

                if self.rect.colliderect(player.rect):
                    self._damage_player(player, self.damage*1.5)

        elif self.state == "dead":
            return

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        if self.state == "dead":
            body_color = (80, 80, 80)
        elif self.state == "lunge_windup":
            pulse = (pygame.time.get_ticks() // 150) % 2 == 0
            body_color = (255, 255, 255) if pulse else self.color
        elif self._phase == 2:
            pulse = (pygame.time.get_ticks() // 200) % 2 == 0
            body_color = (255, 60, 20) if pulse else (255, 140, 20)
        else:
            body_color = self.color

        pygame.draw.rect(screen, body_color, draw_rect)
        pygame.draw.rect(screen, (255, 255, 120), draw_rect, 4)
        self._draw_boss_hud(screen)

    def _draw_boss_hud(self, screen):
        sw, sh = screen.get_size()

        bar_w = int(sw * 0.6)
        bar_h = 28
        bar_x = (sw - bar_w) // 2
        bar_y = sh - 60

        ratio = max(0.0, self.health / max(1, self._initial_health))
        fill_w = int(bar_w * ratio)
        hp_color = (220, 60, 60) if self._phase == 2 else (255, 180, 20)

        panel_padding = 18
        panel = pygame.Rect(
            bar_x - panel_padding,
            bar_y - 40,
            bar_w + panel_padding * 2,
            bar_h + 56
        )
        panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        panel_surf.fill((10, 10, 15, 200))
        screen.blit(panel_surf, panel.topleft)
        pygame.draw.rect(screen, (80, 70, 30), panel, 1)

        font = pygame.font.SysFont("Arial", 20, bold=True)
        label = font.render("WARDEN", True, (255, 220, 80))
        screen.blit(label, (bar_x, bar_y - 30))

        pygame.draw.rect(screen, (30, 30, 35), (bar_x, bar_y, bar_w, bar_h))

        if fill_w > 0:
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h))
            highlight = pygame.Surface((fill_w, bar_h // 2), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 35))
            screen.blit(highlight, (bar_x, bar_y))

        pygame.draw.rect(screen, (180, 150, 40), (bar_x, bar_y, bar_w, bar_h), 2)

        hp_font = pygame.font.SysFont("Arial", 15, bold=True)
        hp_text = hp_font.render(f"{max(0, int(self.health))} / {self._initial_health}", True, (220, 220, 220))
        tx = bar_x + (bar_w - hp_text.get_width()) // 2
        ty = bar_y + (bar_h - hp_text.get_height()) // 2
        screen.blit(hp_text, (tx, ty))

    # ---- HELPERS ----

    def _update_phase(self):
        if self._phase == 1 and self.health <= self._initial_health * 0.5:
            self._phase = 2
            self.speed = 130
            self._MINION_CAP = self._MINION_CAP_PHASE2

    def _try_spawn(self, room, now):
        if now < self._next_spawn_at:
            return

        live = len(self.pending_spawns)
        if live >= self._MINION_CAP:
            self._next_spawn_at = now + 1000
            return

        count = random.randint(2, 3)
        minion_cls = FastEnemy if self._phase == 2 else SwarmEnemy
        for _ in range(count):
            spawn_tile = self._pick_random_free_tile(room, self._grid_pos(), 2)
            if spawn_tile is None:
                continue
            self.pending_spawns.append(
                (minion_cls, *self._center_of_tile(*spawn_tile))
            )

        interval = self._PHASE2_SPAWN_INTERVAL if self._phase == 2 else self._PHASE1_SPAWN_INTERVAL
        self._next_spawn_at = now + interval