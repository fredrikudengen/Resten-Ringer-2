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

    def draw(self, screen, camera):
        """
        Tegn spilleren med spesiell farge når den angriper.
        
        Args:
            screen: pygame Surface
            camera: Camera objekt
        """
        draw_rect = camera.apply(self.rect)
        color = constants.RED if self.playerAttack else self.color
        pygame.draw.rect(screen, color, draw_rect)