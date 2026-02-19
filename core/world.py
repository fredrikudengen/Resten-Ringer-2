import pygame
import constants
from entities import Enemy
from components import Particle
import random


class World:
    """
    World manager - håndterer alle game entities og komponenter.
    
    Dette er "Entity Component System"-lignende design hvor World
    holder lister av entities og oppdaterer dem polymorfisk.
    
    OPPDATERT: Støtter nå forskjellige enemy types!
    """
    
    def __init__(self):
        # Static geometry
        self.obstacles = []
        
        # Entities (alle arver fra Entity base class)
        self.enemies = []
        
        # Components (ikke entities)
        self.powerups = []
        self.particles = []
        self.projectiles = []
        
        # Room reference
        self.current_room = None

    # ---------- World content management ----------
    
    def clear(self):
        """Fjern alt innhold fra world."""
        self.obstacles.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.projectiles.clear()

    def load_blueprint(self, bp: dict):
        """
        Last inn et rom-blueprint.
        
        Args:
            bp: Dictionary med:
                - "obstacles": Liste av pygame.Rect
                - "enemies": Liste av (x, y, enemy_type) eller (x, y, w, h) tuples
                - "powerups": Liste av powerup objekter
                
        Enemy format:
            - (x, y) → Spawner default Enemy
            - (x, y, "FastEnemy") → Spawner FastEnemy
            - (x, y, FastEnemy) → Spawner FastEnemy (class)
        """
        self.clear()
        
        for r in bp.get("obstacles", []):
            self.obstacles.append(r)
            
        for e in bp.get("enemies", []):
            if len(e) == 2:
                # (x, y) → default Enemy
                x, y = e
                self.enemies.append(Enemy(x, y))
            elif len(e) == 3:
                # (x, y, enemy_type)
                x, y, enemy_type = e
                self.add_enemy(x, y, enemy_type=enemy_type)
            elif len(e) == 4:
                # Legacy format: (x, y, w, h) → ignore w, h
                x, y, w, h = e
                self.enemies.append(Enemy(x, y))
            
        for p in bp.get("powerups", []):
            self.powerups.append(p)

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

    def update(self, dt_ms: int, player, camera):
        """
        Oppdater alle entities og components.
        
        Dette er hvor polymorfisme skinner! Alle enemies oppdateres
        på samme måte uavhengig av spesifikk type.
        
        Args:
            dt_ms: Delta time i millisekunder
            player: Player entity
            camera: Camera objekt
        """
        # Oppdater fiender (polymorfisk!)
        for enemy in self.enemies[:]:
            enemy.move(player, self.obstacles, self.current_room, dt_ms)
            enemy._apply_separation(self.enemies)
            
            # Håndter hit feedback
            if enemy.hit:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=5)
                enemy.hit = False
            
            # Fjern døde fiender
            if not enemy.alive:
                self.spawn_hit_particles(enemy.rect.centerx, enemy.rect.centery, n=10)
                self.enemies.remove(enemy)

        # Oppdater projectiles
        for projectile in self.projectiles[:]:
            projectile.update(dt_ms, self.obstacles)

            # Sjekk treff på fiender (polymorfisk kollisjon!)
            for enemy in self.enemies:
                if projectile.rect.colliderect(enemy.rect):
                    enemy.health -= projectile.damage
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

    # ---------- Enemy Spawning Helpers ----------
    
    def spawn_wave(self, n, area_rect: pygame.Rect, enemy_type=None, mixed=False):
        """
        Spawn en bølge av fiender i et område.
        
        Args:
            n: Antall fiender å spawne
            area_rect: Område å spawne innenfor
            enemy_type: Spesifikk enemy type (None = default Enemy)
            mixed: Hvis True, spawn blandet bølge (ignorer enemy_type)
        
        Eksempler:
            world.spawn_wave(5, area)                      # 5 default enemies
            world.spawn_wave(5, area, "FastEnemy")        # 5 FastEnemies
            world.spawn_wave(5, area, FastEnemy)          # 5 FastEnemies
            world.spawn_wave(10, area, mixed=True)        # 10 blandede enemies
        """
        if mixed:
            # Bruk utility function for blandet bølge
            spawn_mixed_wave(self, area_rect, count=n)
        else:
            # Spawn spesifikk type
            for _ in range(n):
                x = random.randint(area_rect.left, area_rect.right - 50)
                y = random.randint(area_rect.top, area_rect.bottom - 50)
                self.add_enemy(x, y, enemy_type=enemy_type)
    
    def spawn_mixed_wave(self, area_rect: pygame.Rect, count=10):
        """
        Spawn en blandet bølge av forskjellige enemy types.
        
        Wrapper rundt utility function.
        
        Args:
            area_rect: Område å spawne innenfor
            count: Antall enemies
        """
        spawn_mixed_wave(self, area_rect, count=count)
    
    def spawn_boss_wave(self, area_rect: pygame.Rect):
        """
        Spawn en boss med minions.
        
        Wrapper rundt utility function.
        
        Args:
            area_rect: Område å spawne innenfor (boss i sentrum)
        """
        spawn_boss_wave(self, area_rect)
    
    def spawn_specific_wave(self, area_rect: pygame.Rect, enemy_types_with_counts):
        """
        Spawn en bølge med spesifikk sammensetning.
        
        Args:
            area_rect: Område å spawne innenfor
            enemy_types_with_counts: Dict eller liste av (enemy_type, count) tuples
        
        Eksempel:
            world.spawn_specific_wave(area, {
                "FastEnemy": 3,
                "SlowEnemy": 2,
                "TankEnemy": 1
            })
            
            eller:
            
            world.spawn_specific_wave(area, [
                (FastEnemy, 3),
                (SlowEnemy, 2),
                (TankEnemy, 1)
            ])
        """
        if isinstance(enemy_types_with_counts, dict):
            items = enemy_types_with_counts.items()
        else:
            items = enemy_types_with_counts
        
        for enemy_type, count in items:
            for _ in range(count):
                x = random.randint(area_rect.left, area_rect.right - 50)
                y = random.randint(area_rect.top, area_rect.bottom - 50)
                self.add_enemy(x, y, enemy_type=enemy_type)
    
    def spawn_circle_formation(self, center_x, center_y, radius, enemy_type, count):
        """
        Spawn enemies i en sirkel rundt et punkt.
        
        Args:
            center_x, center_y: Senter av sirkelen
            radius: Radius i piksler
            enemy_type: Type enemy å spawne
            count: Antall enemies
        
        Eksempel:
            world.spawn_circle_formation(400, 300, 100, "FastEnemy", 8)
        """
        import math
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            self.add_enemy(x, y, enemy_type=enemy_type)
    
    def spawn_line_formation(self, start_x, start_y, end_x, end_y, enemy_type, count):
        """
        Spawn enemies i en linje.
        
        Args:
            start_x, start_y: Start punkt
            end_x, end_y: Slutt punkt
            enemy_type: Type enemy å spawne
            count: Antall enemies
        
        Eksempel:
            world.spawn_line_formation(100, 100, 500, 100, "SlowEnemy", 5)
        """
        for i in range(count):
            t = i / max(count - 1, 1)  # 0.0 til 1.0
            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t)
            self.add_enemy(x, y, enemy_type=enemy_type)

    # ---------- Helpers ----------
    
    def get_all_entities(self):
        """
        Hent alle entities i world.
        
        Nyttig for collision detection eller andre systemer som
        trenger å se alle entities på en gang.
        
        Returns:
            list: Liste av alle Entity objekter
        """
        return self.enemies[:]
    
    def count_alive_enemies(self):
        """
        Tell levende fiender.
        
        Returns:
            int: Antall levende fiender
        """
        return sum(1 for e in self.enemies if e.alive)
    
    def count_enemies_by_type(self):
        """
        Tell fiender gruppert etter type.
        
        Returns:
            dict: {enemy_class_name: count}
        
        Eksempel:
            {
                "FastEnemy": 3,
                "SlowEnemy": 2,
                "BossEnemy": 1
            }
        """
        counts = {}
        for enemy in self.enemies:
            if enemy.alive:
                class_name = enemy.__class__.__name__
                counts[class_name] = counts.get(class_name, 0) + 1
        return counts
    
    def get_enemies_of_type(self, enemy_type):
        """
        Hent alle fiender av en spesifikk type.
        
        Args:
            enemy_type: Enemy class eller string name
        
        Returns:
            list: Liste av enemies av denne typen
        
        Eksempel:
            fast_enemies = world.get_enemies_of_type("FastEnemy")
            bosses = world.get_enemies_of_type(BossEnemy)
        """
        if isinstance(enemy_type, str):
            enemy_class = self._resolve_enemy_type(enemy_type)
        else:
            enemy_class = enemy_type
        
        return [e for e in self.enemies if isinstance(e, enemy_class) and e.alive]
    
    def _resolve_enemy_type(self, type_name: str):
        """
        Resolve enemy type string til class.
        
        Args:
            type_name: String name av enemy type
        
        Returns:
            Enemy class
        """
        # Import enemy types dynamisk
        from entities import (
            Enemy, FastEnemy, SlowEnemy, TankEnemy,
            ScoutEnemy, AssassinEnemy, BruteEnemy,
            SwarmEnemy, BossEnemy
        )
        
        type_map = {
            "Enemy": Enemy,
            "FastEnemy": FastEnemy,
            "SlowEnemy": SlowEnemy,
            "TankEnemy": TankEnemy,
            "ScoutEnemy": ScoutEnemy,
            "AssassinEnemy": AssassinEnemy,
            "BruteEnemy": BruteEnemy,
            "SwarmEnemy": SwarmEnemy,
            "BossEnemy": BossEnemy,
        }
        
        if type_name in type_map:
            return type_map[type_name]
        else:
            # Fallback til default Enemy
            print(f"Warning: Unknown enemy type '{type_name}', using default Enemy")
            return Enemy