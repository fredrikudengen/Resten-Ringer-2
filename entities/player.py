import pygame
from core import constants
from .entity import Entity
from components.gun import Pistol, Shotgun, MachineGun, SniperRifle
from gamestates.char_select import CHARACTERS
from core.sound_manager import sound

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
        self.hit = False
        self.hit_timer = None
        char = CHARACTERS[selected_character]

        self.max_health = char.get('max_health')
        self.health     = self.max_health
        self.alive      = True
        self.speed      = char.get('speed')
        self.width      = char.get('size')[0]
        self.height     = char.get('size')[1]
        self.dash_cooldown = char.get('dash_cooldown')
        self.dash_speed = char.get('dash_speed')
        self.knockback_friction = 0.75

        super().__init__(x=0, y=0)

        self.selected_character = selected_character
        self.char_name          = char['name']
        self.color              = char.get('color', constants.PLAYER_COLOR)
        self.is_moving          = False
        self.total_kills       = 0

        # Gun — resolved from string name via _GUN_MAP
        gun_key    = char.get('gun', 'Shotgun')
        gun_class  = _GUN_MAP.get(gun_key, Shotgun)
        self.gun   = gun_class()

        # Per-character dash timings
        self._dash_duration = constants.DASH_DURATION
        self.dash_cooldown = char.get('dash_cooldown')

        # Attack / debug
        self.debug_attack_rect  = None
        self.debug_attack_until = 0

        # Buffs
        self.buff_timers: dict[str, int] = {}
        self.relics: list = []
        self.adrenaline_until: int = 0

        # Dash
        self.is_dashing        = False
        self.dash_direction    = pygame.math.Vector2(0, 0)
        self.dash_end_time     = 0
        self.dash_cooldown_end = 0

        # Damage / knockback
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
        elif self.is_invincible:
            color = constants.BLUE
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

        for relic in self.relics:
            relic.on_dash(self)

        self.is_dashing        = True
        self.dash_direction    = direction.normalize()
        self.dash_end_time     = now + self._dash_duration
        self.dash_cooldown_end = now + self.dash_cooldown

        sound.play("dash")

    def update_dash(self, obstacles):
        """Update dash movement. Call every frame."""
        now = pygame.time.get_ticks()
        if not self.is_dashing:
            return
        if now >= self.dash_end_time:
            self.is_dashing = False
            return

        dx = int(self.dash_direction.x * self.dash_speed)
        dy = int(self.dash_direction.y * self.dash_speed)

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

    def add_relic(self, relic_class):
        relic = relic_class()
        self.relics.append(relic)
        relic.on_equip(self)

    def update_relics(self):
        now = pygame.time.get_ticks()
        if self.adrenaline_until and now >= self.adrenaline_until:
            self.speed -= 3
            self.adrenaline_until = 0

    # ========== HELPERS ==========

    def _level_up(self):
        """Handle one level-up: update stats and notify the HUD."""
        self.level += 1

        self.health     += constants.XP_HP_BONUS_PER_LEVEL
        self.max_health += constants.XP_HP_BONUS_PER_LEVEL
        self.gun.damage += constants.XP_DPS_BONUS_PER_LEVEL

        if self._hud is not None:
            self._hud.notify_levelup(self.level)