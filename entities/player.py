import pygame
import constants
from .entity import Entity

class Player(Entity):
    
    def __init__(self, x, y):
        """
        Initialiser spiller.
        
        Args:
            x, y: Startposisjon
        """
        self.width=constants.PLAYER_SIZE[0]
        self.height=constants.PLAYER_SIZE[1]

        super().__init__(x, y)

        self.speed=constants.PLAYER_SPEED
        self.health=constants.PLAYER_HEALTH
        self.color=constants.PLAYER_COLOR
        self.dps = constants.PLAYER_DPS
        
        # Angrep / debug
        self.attack_cooldown    = constants.PLAYER_ATTACK_COOLDOWN
        self.playerAttack       = False
        self.debug_attack_rect  = None
        self.debug_attack_until = 0

        # Buffs system
        self.buff_timers = {}

        # Dash
        self.is_dashing        = False
        self.dash_direction    = pygame.math.Vector2(0, 0)
        self.dash_end_time     = 0
        self.dash_cooldown_end = 0

        # Skade / knockback
        self.knockback_velocity    = pygame.math.Vector2(0, 0)
        self.hurt_invincible_until = 0  

        # XP og level
        self.xp    = 0
        self.level = 1
        self._hud  = None   # Settes av main.py: player._hud = hud

    @property
    def is_invincible(self):
        """
        True når spilleren ikke kan ta skade.
        Dekker både dash-iframes og post-hit iframes.
        """
        now = pygame.time.get_ticks()
        return self.is_dashing or now < self.hurt_invincible_until
    
    @property
    def xp_to_next(self) -> int:
        """
        XP som trengs for neste level.
        Formelen skalerer progressivt: 100, 150, 225, …
        """
        return int(constants.XP_BASE * (constants.XP_SCALE ** (self.level - 1)))

    # ── XP / Level ────────────────────────────────────────

    def gain_xp(self, amount: int):
        """
        Gi spilleren XP. Håndterer level-up automatisk og varsler HUD.

        Args:
            amount: Mengde XP å legge til
        """
        if amount <= 0:
            return

        self.xp += amount

        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self._level_up()

    def _level_up(self):
        """Håndter ett level-opp: oppdater stats og varsle HUD."""
        self.level += 1

        bonus_hp = constants.XP_HP_BONUS_PER_LEVEL
        self.health = min(self.health + bonus_hp, constants.PLAYER_HEALTH + bonus_hp * self.level)

        bonus_dps = constants.XP_DPS_BONUS_PER_LEVEL
        self.dps = min(self.dps + bonus_dps, constants.PLAYER_DPS + bonus_dps * self.level)

        bonus_speed = constants.XP_SPEED_BONUS_PER_LEVEL
        self.speed = min(self.speed + bonus_speed, constants.PLAYER_SPEED + bonus_speed * self.level)


        if self._hud is not None:
            self._hud.notify_levelup(self.level)

    def update_knockback(self, obstacles):
        """
        Bruk knockback-bevegelse med friksjon. Kalles hver frame.

        Args:
            obstacles: Liste av hindringer for kollisjonsjekk
        """
        if self.knockback_velocity.length_squared() < 0.5:
            self.knockback_velocity.update(0, 0)
            return

        # Flytt x
        old_x = self.rect.x
        self.rect.x += int(self.knockback_velocity.x)
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.x = old_x
            self.knockback_velocity.x = 0

        # Flytt y
        old_y = self.rect.y
        self.rect.y += int(self.knockback_velocity.y)
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.y = old_y
            self.knockback_velocity.y = 0

        self.sync_pos_from_rect()

        # Demping
        self.knockback_velocity *= constants.PLAYER_KNOCKBACK_FRICTION
    
    def check_collision_obstacle(self, obstacles):
        """
        Legacy metode for bakoverkompatibilitet.
        Wrapper rundt Entity.check_collision()
        """
        return self.check_collision(obstacles)
    
    BUFF_VALUES = {
    'speed_boost':  ('speed',  3),
    'attack_boost': ('dps',    1),
    'shield_boost': ('health', 2),
}

    def apply_powerup(self, powerup):
        if powerup in self.buff_timers:
            return
        attr, value = self.BUFF_VALUES[powerup]
        setattr(self, attr, getattr(self, attr) + value)
        self.buff_timers[powerup] = pygame.time.get_ticks()

    def update_powerups(self):
        now = pygame.time.get_ticks()
        for name, start in list(self.buff_timers.items()):
            if now - start >= constants.BUFF_DURATIONS.get(name, 0):
                attr, value = self.BUFF_VALUES[name]
                setattr(self, attr, getattr(self, attr) - value)
                del self.buff_timers[name]

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

        self.is_dashing        = True
        self.dash_direction    = direction.normalize()
        self.dash_end_time     = now + constants.DASH_DURATION
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

        # collision check x
        old_x = self.rect.x
        self.rect.x += dx
        if any(self.rect.colliderect(obs) for obs in obstacles):
            self.rect.x = old_x
            self.is_dashing = False

        # collision check y
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