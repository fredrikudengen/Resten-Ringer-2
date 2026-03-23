import pygame
from pygame.math import Vector2
from core import constants

class Entity:
    
    def __init__(self, x, y):
        """
        Initialiser entity.
        
        Args:
            x, y: Startposisjon (top-left)
            width, height: Størrelse
            """
        self.knockback_friction = 0.85
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.pos  = Vector2(self.rect.center)
        self.knockback_velocity    = pygame.math.Vector2(0, 0)

    def draw(self, screen, camera):
        """
        Tegn entity. Override for custom tegning.
        
        Args:
            screen: pygame Surface
            camera: Camera objekt med .apply(rect) metode
        """

    def check_collision(self, obstacles):
        """
        Sjekk kollisjon med obstacles.
        
        Args:
            obstacles: Liste av pygame.Rect objekter
            
        Returns:
            bool: True hvis kollisjon, False ellers
        """
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False
    
    def check_collision_entity(self, other):
        """
        Sjekk kollisjon med en annen entity.
        
        Args:
            other: En annen Entity instans
            
        Returns:
            bool: True hvis kollisjon
        """
        return self.rect.colliderect(other.rect)
    
    def _grid_pos(self):
        """
        Returner grid-koordinat (gx, gy) basert på TILE_SIZE.
        
        Returns:
            tuple: (grid_x, grid_y)
        """
        T = constants.TILE_SIZE
        return (int(self.pos.x) // T, int(self.pos.y) // T)
    
    def _sync_rect_from_pos(self):
        """
        Synkroniser heltalls-rect fra float-posisjon (senter).
        Viktig for smooth subpixel bevegelse!
        """
        self.rect.centerx = int(round(self.pos.x))
        self.rect.centery = int(round(self.pos.y))
    
    def sync_pos_from_rect(self):
        """Synkroniser pos fra rect etter bevegelse."""
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
    
    def _center_of_tile(self, gx, gy):
        """
        Returner piksel-senteret til grid-ruten (gx, gy).
        
        Args:
            gx, gy: Grid koordinater
            
        Returns:
            tuple: (pixel_x, pixel_y)
        """
        T = constants.TILE_SIZE
        return (gx * T + T // 2, gy * T + T // 2)
    
    def _dist2(self, a1, a2, b1, b2):
        """
        Kvadrert euklidisk distanse (unngår sqrt for performance).
        
        Args:
            a1, a2: Første punkt (x, y)
            b1, b2: Andre punkt (x, y)
            
        Returns:
            int: Kvadrert distanse
        """
        dx, dy = a1 - b1, a2 - b2
        return dx * dx + dy * dy

    def update_knockback(self, obstacles):
        """Apply knockback velocity with friction. Call every frame."""
        if self.knockback_velocity.length_squared() < 0.5:
            self.knockback_velocity.update(0, 0)
            return

        old_x = self.rect.x
        self.rect.x += int(self.knockback_velocity.x)
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.x = old_x
            self.knockback_velocity.x = 0

        old_y = self.rect.y
        self.rect.y += int(self.knockback_velocity.y)
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.y = old_y
            self.knockback_velocity.y = 0

        self.sync_pos_from_rect()
        self.knockback_velocity *= self.knockback_friction

    def apply_knockback(self, source_rect, strength):
        direction = pygame.math.Vector2(
                self.rect.centerx - source_rect.centerx,
                self.rect.centery - source_rect.centery
        )
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(1, 0)
        self.knockback_velocity = direction * strength