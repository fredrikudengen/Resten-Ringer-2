import pygame
import constants
from entities import enemies
from entities import Enemy
from components import Particle
import random
from entities import ENEMY_TYPES


class World:
    
    def __init__(self):
        self.obstacles = []
        self.enemies = []
        self.powerups    = []
        self.particles   = []
        self.projectiles = []
        self.current_room = None

    def update(self, dt_ms: int, player):
        """
        Oppdater alle entities og components.
        
        Dette er hvor polymorfisme skinner! Alle enemies oppdateres
        på samme måte uavhengig av spesifikk type.
        
        Args:
            dt_ms: Delta time i millisekunder
            player: Player entity
            camera: Camera objekt
        """
        for enemy in self.enemies[:]:
            enemy.move(player, self.obstacles, self.current_room, dt_ms)
            enemy._apply_separation(self.enemies)
            
            if enemy.hit:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=5)
                enemy.hit = False
            
            if not enemy.alive:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=10)
                player.gain_xp(enemy.xp_reward)
                self.enemies.remove(enemy)

        for projectile in self.projectiles[:]:
            projectile.update(dt_ms, self.obstacles)

            for enemy in self.enemies:
                if projectile.rect.colliderect(enemy.rect):
                    enemy.health -= player.dps
                    enemy.hit = True
                    projectile.alive = False
                    break
            
            if not projectile.alive:
                self.projectiles.remove(projectile)

        # Oppdater powerups (kollisjon med player)
        for pu in self.powerups[:]:
            if player.rect.colliderect(pu.rect):
                pu.apply(player)
                self.powerups.remove(pu)

        # Oppdater particles
        for p in self.particles[:]:
            p.update(dt_ms)
            if p.timer <= 0:
                self.particles.remove(p)

    def draw(self, screen, camera):
        """
        Tegn alle entities og komponenter.
        
        Polymorfisme igjen: alle entities har .draw() metode!
        
        Args:
            screen: pygame Surface
            camera: Camera objekt
        """
        if not hasattr(self, "current_room") or self.current_room is None:
            return

        # Tegn terrain grid
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
        
        # Tegn obstacles
        for obstacle in self.obstacles:
            sr = camera.apply(obstacle)
            pygame.draw.rect(screen, (128, 128, 128), sr)

        # Tegn powerups
        for pu in self.powerups:
            pu.draw(screen, camera)

        # Tegn enemies (polymorfisk!)
        for e in self.enemies:
            e.draw(screen, camera)
        
        # Tegn projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, camera)

        # Tegn particles
        for p in self.particles:
            p.draw(screen, camera)

    # ---------- World content management ----------
    
    def clear(self):
        """Fjern alt innhold fra world."""
        self.obstacles.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.projectiles.clear()

    # ---------- Public API ----------
    
    def add_obstacle(self, rect: pygame.Rect):
        """Legg til en obstacle i world."""
        self.obstacles.append(rect)

    def add_enemy(self, x, y, enemy_type=None):
        """
        Spawn en ny fiende.
        
        Args:
            x, y: Spawn posisjon
            enemy_type: Enemy class eller string name (f.eks. "FastEnemy")
                       None = default Enemy
        
        Eksempler:
            world.add_enemy(100, 100)                          # Default Enemy
            world.add_enemy(100, 100, "FastEnemy")            # FastEnemy by string
            world.add_enemy(100, 100, FastEnemy)              # FastEnemy by class
            world.add_enemy(100, 100, enemy_type=SlowEnemy)  # SlowEnemy
        """
        if enemy_type is None:
            # Default Enemy
            self.enemies.append(Enemy(x, y))
        elif isinstance(enemy_type, str):
            # String name - resolve dynamisk
            enemy_class = self._resolve_enemy_type(enemy_type)
            self.enemies.append(enemy_class(x, y))
        else:
            # Antatt at det er en class
            self.enemies.append(enemy_type(x, y))

    def add_powerup(self, powerup):
        """Legg til en power-up i world."""
        self.powerups.append(powerup)

    def spawn_hit_particles(self, x, y, n=5, color=constants.YELLOW):
        """
        Spawn partikler ved en posisjon (f.eks. ved treff).
        
        Args:
            x, y: Spawn posisjon
            n: Antall partikler
            color: Farge på partikler
        """
        for _ in range(n):
            self.particles.append(Particle(x, y, color))
    
    def _resolve_enemy_type(self, type_name: str):
        """
        Resolve enemy type string til class.
        
        Args:
            type_name: String name av enemy type
        
        Returns:
            Enemy class
        """
        if type_name in ENEMY_TYPES:
            return ENEMY_TYPES[type_name]
        else:
            # Fallback til default Enemy
            print(f"Warning: Unknown enemy type '{type_name}', using default Enemy")
            return ENEMY_TYPES["Enemy"]