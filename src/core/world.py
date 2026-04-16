import pygame

from components.power_up import BasePowerup, POWERUP_TYPES
from core import constants
from view.sound_manager import sound
from entities import WardenBoss
from entities import Enemy
from components import Particle
from components.bullet import Bullet
from entities import ENEMY_TYPES


class World:

    def __init__(self):
        self.obstacles:   list[pygame.Rect] = []
        self.enemies:     list              = []
        self.powerups:    list              = []
        self.particles:   list              = []
        self.bullets:     list[Bullet]      = []
        self.current_room = None

    # =========== PUBLIC API ===========

    def update(self, dt_ms, player, obstacles):

        # -- Enemies --
        for enemy in self.enemies[:]:

            enemy.move(player, self.obstacles, self.current_room, dt_ms)
            enemy.apply_separation(self.enemies, obstacles)

            pending = getattr(enemy, 'pending_bullets', None)
            if pending:
                self.bullets.extend(pending)
                pending.clear()

            spawns = getattr(enemy, 'pending_spawns', None)
            cap = getattr(enemy, '_MINION_CAP', None)
            if spawns and (len(self.enemies) < cap):
                for cls, sx, sy in spawns:
                    self.add_enemy(sx, sy, enemy_type=cls)
                spawns.clear()

            if enemy.hit:
                sound.play("enemy/hit")

            if isinstance(enemy, WardenBoss) and not enemy.alive:
                self.enemies.clear()
            elif not enemy.alive:
                self._spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=10)
                player.gain_xp(enemy.xp_reward)
                player.total_kills += 1
                for relic in player.relics:
                    relic.on_kill(player)

                sound.play("enemy/die")
                self.enemies.remove(enemy)

            enemy.hit = False

        # -- Bullets --
        for bullet in self.bullets[:]:
            bullet.update(dt_ms, self.obstacles)

            if not bullet.alive:
                self.bullets.remove(bullet)
                continue

            for enemy in self.enemies:
                if bullet.team == "player" and bullet.rect.colliderect(enemy.rect):
                    bullet.damage_enemy(enemy)
                    break

            if (bullet.team == "enemy" and
                    not player.is_invincible
                    and bullet.rect.colliderect(player.rect)):
                bullet.damage_player(player)

            if not bullet.alive and bullet in self.bullets:
                self.bullets.remove(bullet)

        # -- Powerups --
        for pu in self.powerups[:]:
            if player.rect.colliderect(pu.rect):
                pu.apply(player)
                sound.play(f"ui/powerup")
                self.powerups.remove(pu)

        # -- Particles --
        for p in self.particles[:]:
            p.update(dt_ms)
            if p.timer <= 0:
                self.particles.remove(p)

        player.hit = False

    def draw(self, screen: pygame.Surface, camera):
        if self.current_room is None:
            return

        room = self.current_room
        for gy in range(room.rows):
            for gx in range(room.cols):
                rect = pygame.Rect(
                    gx * constants.TILE_SIZE,
                    gy * constants.TILE_SIZE,
                    constants.TILE_SIZE,
                    constants.TILE_SIZE,
                )
                dr = camera.apply(rect)
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    pygame.draw.rect(screen, constants.TILE_WALL_COLOR, dr)
                else:
                    pygame.draw.rect(screen, constants.TILE_FLOOR_COLOR, dr)

        for pu in self.powerups:
            pu.draw(screen, camera)

        for enemy in self.enemies:
            enemy.draw(screen, camera)

        for bullet in self.bullets:
            bullet.draw(screen, camera)

        for p in self.particles:
            p.draw(screen, camera)

    def add_bullets(self, bullets: list[Bullet]):
        for b in bullets:
            b.source = 'player'
        self.bullets.extend(bullets)

    def clear(self):
        self.obstacles.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.bullets.clear()

    def add_obstacle(self, rect: pygame.Rect):
        self.obstacles.append(rect)

    def add_enemy(self, x, y, enemy_type=None):
        if enemy_type is None:
            enemy = Enemy(x, y)
        elif isinstance(enemy_type, str):
            enemy = self._resolve_enemy_type(enemy_type)(x, y)
        else:
            enemy = enemy_type(x, y)
        self.enemies.append(enemy)
        return enemy

    def add_powerup(self, powerup_or_x, y=None, powerup_type=None):
        if isinstance(powerup_or_x, BasePowerup):
            self.powerups.append(powerup_or_x)
            return powerup_or_x
        x = powerup_or_x
        if powerup_type is None:
            powerup = BasePowerup(x, y)
        elif isinstance(powerup_type, str):
            powerup = self._resolve_powerup_type(powerup_type)(x, y)
        else:
            powerup = powerup_type(x, y)
        self.powerups.append(powerup)
        return powerup

    # ---------- HELPERS ----------

    def _spawn_hit_particles(self, x, y, n=5, color=constants.YELLOW):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def _resolve_enemy_type(self, type_name: str):
        if type_name in ENEMY_TYPES:
            return ENEMY_TYPES[type_name]
        print(f"Warning: unknown enemy type '{type_name}', falling back to Enemy")
        return ENEMY_TYPES["Enemy"]

    def _resolve_powerup_type(self, type_name: str):
        if type_name in POWERUP_TYPES:
            return POWERUP_TYPES
        print(f"Warning: unknown powerup type '{type_name}', falling back to Powerup")
        return POWERUP_TYPES["Powerup"]
