import pygame
from core import constants
from entities import enemies
from entities import Enemy
from components import Particle
from components.bullet import Bullet
import random
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

    def update(self, dt_ms: int, player):
        """Update all entities and components."""

        # -- Enemies --
        for enemy in self.enemies[:]:
            enemy.move(player, self.obstacles, self.current_room, dt_ms)
            enemy._apply_separation(self.enemies)

            if enemy.hit:
                self._spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=5)

            if not enemy.alive:
                self._spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=10)
                player.gain_xp(enemy.xp_reward)
                self.enemies.remove(enemy)

        # -- Bullets --
        for bullet in self.bullets[:]:
            bullet.update(dt_ms, self.obstacles)

            if not bullet.alive:
                self.bullets.remove(bullet)
                continue

            piercing = getattr(bullet, 'piercing', False)
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    enemy.health -= bullet.damage
                    enemy.hit     = True
                    if not piercing:
                        bullet.alive = False
                        break

            if not bullet.alive:
                self.bullets.remove(bullet)

        # -- Powerups --
        for pu in self.powerups[:]:
            if player.rect.colliderect(pu.rect):
                pu.apply(player)
                self.powerups.remove(pu)

        # -- Particles --
        for p in self.particles[:]:
            p.update(dt_ms)
            if p.timer <= 0:
                self.particles.remove(p)

    def draw(self, screen: pygame.Surface, camera):
        """Draw all entities and components."""
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
        """Add a list of bullets to the world (returned by gun.shoot())."""
        self.bullets.extend(bullets)

    def clear(self):
        """Remove all content from the world."""
        self.obstacles.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.bullets.clear()

    def add_obstacle(self, rect: pygame.Rect):
        self.obstacles.append(rect)

    def add_enemy(self, x, y, enemy_type=None):
        if enemy_type is None:
            self.enemies.append(Enemy(x, y))
        elif isinstance(enemy_type, str):
            self.enemies.append(self._resolve_enemy_type(enemy_type)(x, y))
        else:
            self.enemies.append(enemy_type(x, y))

    def add_powerup(self, powerup):
        self.powerups.append(powerup)

    # =========== HELPERS ===========

    def _spawn_hit_particles(self, x, y, n=5, color=constants.YELLOW):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def _resolve_enemy_type(self, type_name: str):
        if type_name in ENEMY_TYPES:
            return ENEMY_TYPES[type_name]
        print(f"Warning: unknown enemy type '{type_name}', falling back to Enemy")
        return ENEMY_TYPES["Enemy"]