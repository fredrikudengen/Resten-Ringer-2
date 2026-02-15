import pygame
import constants

class Player:
    def __init__(self, x, y,):
        self.rect = pygame.Rect(x, y, *constants.PLAYER_SIZE)
        self.color = constants.PLAYER_COLOR
        self.speed = constants.PLAYER_SPEED
        self.health = constants.PLAYER_HEALTH
        self.dps = constants.PLAYER_DPS
        self.alive = constants.ALIVE

        # Angrep / debug
        self.attack_cooldown = constants.PLAYER_ATTACK_COOLDOWN
        self.playerAttack = False
        self.debug_attack_rect = None
        self.debug_attack_until = 0

        # Buffs
        self.buff_timers = {}
    
    def check_collision_obstacle(self, obstacles):
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                return True
        return False
    
    def check_collision_enemy(self, enemies):
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                return True
        return False
    
    def apply_buff(self, powerup):
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
        now = pygame.time.get_ticks()
        expired = []
        for name, start in list(self.buff_timers.items()):
            duration = constants.BUFF_DURATIONS.get(name, 0)
            if now - start >= duration:
                expired.append(name)

        # Fjern effekt
        for name in expired:
            if name == 'speed_boost':
                self.speed -= 3
            elif name == 'attack_boost':
                self.dps -= 1
            elif name == 'shield_boost':
                self.health -= 2
            self.buff_timers.pop(name)
            
    def _grid_pos(self):
        """Returner grid-koordinat (gx, gy) basert på TILE_SIZE."""
        T = constants.TILE_SIZE
        return (int(self.rect.centerx) // T, int(self.rect.centery) // T)

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        color = constants.RED if self.playerAttack else self.color
        pygame.draw.rect(screen, color, draw_rect)