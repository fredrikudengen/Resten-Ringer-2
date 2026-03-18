import pygame
from core import constants
from .entity import Entity
from components import Pistol, Shotgun, MachineGun, SniperRifle
from gamestates.char_select import CHARACTERS

_GUN_MAP = {
    'Pistol':      Pistol,
    'Shotgun':     Shotgun,
    'MachineGun':  MachineGun,
    'SniperRifle': SniperRifle,
}

class Player(Entity):
    """
    The player entity. Stats are seeded from the selected character,
    with fallback defaults from constants.
    """

    def __init__(self, selected_character: int = 0, hud=None):
        char = CHARACTERS[selected_character]

        self.health     = char.get('health', constants.PLAYER_HEALTH)
        self.max_health = self.health
        self.alive      = True
        self.speed      = char.get('speed',  constants.PLAYER_SPEED)
        self.width      = constants.PLAYER_SIZE[0]
        self.height     = constants.PLAYER_SIZE[1]

        super().__init__(x=0, y=0)

        self.selected_character = selected_character
        self.char_name          = char['name']
        self.color              = char.get('color', constants.PLAYER_COLOR)
        self.dps                = constants.PLAYER_DPS
        self.is_moving          = False
        self.total_kills       = 0

        # Gun — resolved from string name via _GUN_MAP
        gun_key    = char.get('gun', 'Shotgun')
        gun_class  = _GUN_MAP.get(gun_key, Shotgun)
        self.gun   = gun_class()

        # Per-character dash timings
        self._dash_duration = constants.DASH_DURATION
        self._dash_cooldown = char.get('dash_cooldown', constants.DASH_COOLDOWN)

        # Attack / debug
        self.attack_cooldown    = constants.PLAYER_ATTACK_COOLDOWN
        self.playerAttack       = False
        self.debug_attack_rect  = None
        self.debug_attack_until = 0

        # Buffs
        self.buff_timers: dict[str, int] = {}

        # Dash
        self.is_dashing        = False
        self.dash_direction    = pygame.math.Vector2(0, 0)
        self.dash_end_time     = 0
        self.dash_cooldown_end = 0

        # Damage / knockback
        self.knockback_velocity    = pygame.math.Vector2(0, 0)
        self.hurt_invincible_until = 0

        # XP and level
        self.xp    = 0
        self.level = 1

        # HUD reference — passed in by StateMachine, not set externally
        self._hud = hud

    @property
    def is_invincible(self):
        """True when the player cannot take damage — covers dash iframes and post-hit iframes."""
        now = pygame.time.get_ticks()
        return self.is_dashing or now < self.hurt_invincible_until

    @property
    def xp_to_next(self) -> int:
        """XP required for the next level. Scales progressively: 100, 150, 225, ..."""
        return int(constants.XP_BASE * (constants.XP_SCALE ** (self.level - 1)))

    # ========== PUBLIC API ==========

    def draw(self, screen, camera):
        """Draw the player, tinting based on current state."""
        draw_rect = camera.apply(self.rect)
        if self.is_dashing:
            color = constants.WHITE
        elif self.playerAttack:
            color = constants.RED
        else:
            color = self.color
        pygame.draw.rect(screen, color, draw_rect)

    def shoot(self, target_pos: tuple[float, float]) -> list:
        """
        Fire the equipped gun toward target_pos.
        Returns a list of Bullet objects to be added to the world.
        """
        direction = pygame.math.Vector2(
            target_pos[0] - self.rect.centerx,
            target_pos[1] - self.rect.centery,
        )
        if direction.length_squared() == 0:
            return []
        return self.gun.shoot(self.rect.center, direction)

    def gain_xp(self, amount: int):
        """Award XP to the player, handling level-ups automatically."""
        if amount <= 0:
            return
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self._level_up()

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
        self.knockback_velocity *= constants.PLAYER_KNOCKBACK_FRICTION

    def apply_powerup(self, powerup):
        if powerup in self.buff_timers:
            return
        attr, value = constants.BUFF_VALUES[powerup]
        setattr(self, attr, getattr(self, attr) + value)
        self.buff_timers[powerup] = pygame.time.get_ticks()

    def update_powerups(self):
        now = pygame.time.get_ticks()
        for name, start in list(self.buff_timers.items()):
            if now - start >= constants.BUFF_DURATIONS.get(name, 0):
                attr, value = constants.BUFF_VALUES[name]
                setattr(self, attr, getattr(self, attr) - value)
                del self.buff_timers[name]

    def start_dash(self, direction: pygame.math.Vector2):
        """Start a dash in the given direction."""
        now = pygame.time.get_ticks()
        if self.is_dashing or now < self.dash_cooldown_end:
            return
        if direction.length_squared() == 0:
            return

        self.is_dashing        = True
        self.dash_direction    = direction.normalize()
        self.dash_end_time     = now + self._dash_duration
        self.dash_cooldown_end = now + self._dash_cooldown

    def update_dash(self, obstacles):
        """Update dash movement. Call every frame."""
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

    # ========== HELPERS ==========

    def _level_up(self):
        """Handle one level-up: update stats and notify the HUD."""
        self.level += 1

        self.health     += constants.XP_HP_BONUS_PER_LEVEL
        self.max_health += constants.XP_HP_BONUS_PER_LEVEL
        self.dps        += constants.XP_DPS_BONUS_PER_LEVEL
        self.speed      += constants.XP_SPEED_BONUS_PER_LEVEL

        if self._hud is not None:
            self._hud.notify_levelup(self.level)