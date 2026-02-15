import pygame
import constants
from entities import Enemy
from components import Particle
import random

class World:
    def __init__(self):
        self.obstacles = []
        self.enemies = []
        self.powerups = []
        self.particles = []
        self.projectiles = []

    # ---------- world content mgmt ----------
    def clear(self):
        self.obstacles.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.projectiles.clear()

    def load_blueprint(self, bp: dict):
        """
        bp = {
          "obstacles": [pygame.Rect(...), ...],
          "enemies":   [(x,y,w,h), ...],
          "powerups":  [powerup_obj, ...]
        }
        """
        self.clear()
        for r in bp.get("obstacles", []):
            self.obstacles.append(r)
        for e in bp.get("enemies", []):
            x, y, w, h = e
            self.enemies.append(Enemy(x, y, w, h))
        for p in bp.get("powerups", []):
            self.powerups.append(p)

    # ---------- public api ----------
    def add_obstacle(self, rect: pygame.Rect):
        self.obstacles.append(rect)

    def add_enemy(self, x, y):
        self.enemies.append(Enemy(x, y))

    def add_powerup(self, powerup):
        self.powerups.append(powerup)

    def spawn_hit_particles(self, x, y, n=5, color=constants.YELLOW):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def update(self, dt_ms: int, player, camera):
        # Enemies
        for enemy in self.enemies[:]:
            enemy.move(player, self.obstacles, self.current_room, dt_ms)
            enemy._apply_separation(self.enemies)
            if enemy.hit:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=5)
                enemy.hit = False
            if not enemy.alive:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=10)
                self.enemies.remove(enemy)

        for projectile in self.projectiles[:]:
            projectile.update(dt_ms, self.obstacles)

            # treff fiender
            for enemy in self.enemies:
                if projectile.rect.colliderect(enemy.rect):
                    enemy.health -= projectile.damage
                    enemy.hit = True
                    projectile.alive = False
                    break
            
            if not projectile.alive:
                self.projectiles.remove(projectile)

        # Powerups
        for pu in self.powerups[:]:
            if player.rect.colliderect(pu.rect):
                pu.apply(player)
                self.powerups.remove(pu)

        # Particles
        for p in self.particles[:]:
            p.update(dt_ms)
            if p.timer <= 0:
                self.particles.remove(p)

    def draw(self, screen, camera):
        if not hasattr(self, "current_room") or self.current_room is None:
            return  # ingenting å tegne

        room = self.current_room
        for gy in range(room.rows):
            for gx in range(room.cols):
                rect = pygame.Rect(
                    gx * constants.TILE_SIZE,
                    gy * constants.TILE_SIZE,
                    constants.TILE_SIZE,
                    constants.TILE_SIZE
                )
                dr = camera.apply(rect)
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    pygame.draw.rect(screen, (80, 80, 80), dr)  # vegg
                else:
                    pygame.draw.rect(screen, (25, 25, 25), dr)  # gulv
        # Obstacles
        for obstacle in self.obstacles:
            sr = camera.apply(obstacle)
            pygame.draw.rect(screen, (128, 128, 128), sr)

        # Powerups
        for pu in self.powerups:
            pu.draw(screen, camera)

        # Enemies
        for e in self.enemies:
            e.draw(screen, camera)
        
        # Projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, camera)

        # Particles
        for p in self.particles:
            p.draw(screen, camera)


        # (Valgfritt) debug: tegn obstacle outlines
        # for obstacle in self.obstacles:
        #     sr = camera.apply(obstacle)
        #     pygame.draw.rect(screen, (200, 200, 200), sr, 1)

    # ---------- helpers ----------
    def _build_room(self):
        """Eksempel på å fylle inn rommet med noen rektangler."""
        # Yttervegger / søyler osv.
        # self.add_obstacle(pygame.Rect(200, 150, 400, 30))
        # self.add_obstacle(pygame.Rect(300, 350, 300, 30))
        # self.add_enemy(200, 200)
        # self.add_enemy(600, 400)
        
    def spawn_wave(self, n, area_rect: pygame.Rect):
        for _ in range(n):
            x = random.randint(area_rect.left, area_rect.right - 50)
            y = random.randint(area_rect.top, area_rect.bottom - 50)
            self.add_enemy(x, y)

