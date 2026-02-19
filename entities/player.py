import pygame
import constants
from .entity import Entity


class Player(Entity):
    """
    Spilleren - styrt av bruker input.
    
    Arver basis-funksjonalitet fra Entity og legger til:
    - Angrep med cooldown
    - Buff-system
    - Spesialisert kollisjonshåndtering
    """
    
    def __init__(self, x, y):
        """
        Initialiser spiller.
        
        Args:
            x, y: Startposisjon
        """
        super().__init__(
            x, y,
            width=constants.PLAYER_SIZE[0],
            height=constants.PLAYER_SIZE[1],
            speed=constants.PLAYER_SPEED,
            health=constants.PLAYER_HEALTH,
            color=constants.PLAYER_COLOR
        )
        
        self.dps = constants.PLAYER_DPS
        
        # Angrep / debug
        self.attack_cooldown = constants.PLAYER_ATTACK_COOLDOWN
        self.playerAttack = False
        self.debug_attack_rect = None
        self.debug_attack_until = 0

        # Buffs system
        self.buff_timers = {}

        # Dash
        self.is_dashing = False
        self.dash_direction = pygame.math.Vector2(0, 0)
        self.dash_end_time = 0
        self.dash_cooldown_end = 0
    
    def check_collision_obstacle(self, obstacles):
        """
        Legacy metode for bakoverkompatibilitet.
        Wrapper rundt Entity.check_collision()
        """
        return self.check_collision(obstacles)
    
    def check_collision_enemy(self, enemies):
        """
        Sjekk kollisjon med fiender.
        
        Args:
            enemies: Liste av Enemy objekter
            
        Returns:
            bool: True hvis kollisjon med noen fiende
        """
        for enemy in enemies:
            if self.check_collision_entity(enemy):
                return True
        return False
    
    def apply_buff(self, powerup):
        """
        Aktiver en power-up buff.
        
        Args:
            powerup: String identifier for buff-type
        """
        now = pygame.time.get_ticks()
        if powerup == 'speed_boost':
            self.speed += 3
            self.buff_timers[powerup] = now
        elif powerup == 'shield_boost':
            self.health += 2
            self.buff_timers[powerup] = now
        elif powerup == 'attack_boost':
            self.dps += 1
            self.buff_timers[powerup] = now
            
    def update_buffs(self):
        """
        Oppdater og fjern utgåtte buffs.
        Kjøres hver frame.
        """
        now = pygame.time.get_ticks()
        expired = []
        
        for name, start in list(self.buff_timers.items()):
            duration = constants.BUFF_DURATIONS.get(name, 0)
            if now - start >= duration:
                expired.append(name)

        # Fjern effekt av utgåtte buffs
        for name in expired:
            if name == 'speed_boost':
                self.speed -= 3
            elif name == 'attack_boost':
                self.dps -= 1
            elif name == 'shield_boost':
                self.health -= 2
            self.buff_timers.pop(name)

    def start_dash(self, direction: pygame.math.Vector2):
        """
        Start en dash i gitt retning.
        
        Args:
            direction: Normalisert retningsvektor for dashen
        """
        now = pygame.time.get_ticks()
        if self.is_dashing or now < self.dash_cooldown_end:
            return 

        if direction.length_squared() == 0:
            return  

        self.is_dashing = True
        self.dash_direction = direction.normalize()
        self.dash_end_time = now + constants.DASH_DURATION
        self.dash_cooldown_end = now + constants.DASH_COOLDOWN
    
    def update_dash(self, obstacles):
        """
        Oppdater dash-bevegelse. Kalles hver frame.
        
        Args:
            obstacles: Liste av hindringer for kollisjonsjekk
        """
        now = pygame.time.get_ticks()
        if not self.is_dashing:
            return

        if now >= self.dash_end_time:
            self.is_dashing = False
            return

        dx = int(self.dash_direction.x * constants.DASH_SPEED)
        dy = int(self.dash_direction.y * constants.DASH_SPEED)

        old_x = self.rect.x
        self.rect.x += dx
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.x = old_x
            self.is_dashing = False

        old_y = self.rect.y
        self.rect.y += dy
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.y = old_y
            self.is_dashing = False

        self.sync_pos_from_rect()

    def draw(self, screen, camera):
        """
        Tegn spilleren med spesiell farge når den angriper.
        
        Args:
            screen: pygame Surface
            camera: Camera objekt
        """
        draw_rect = camera.apply(self.rect)
        if self.is_dashing:
            color = constants.WHITE
        elif self.playerAttack:
            color = constants.RED
        else:
            color = self.color
        pygame.draw.rect(screen, color, draw_rect)
    
    @property
    def is_invincible(self):
        return self.is_dashing