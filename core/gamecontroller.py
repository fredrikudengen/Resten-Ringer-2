import pygame
import constants

from components import Projectile


def player_input(player, obstacles, world, camera):
    keys = pygame.key.get_pressed()
    now = pygame.time.get_ticks()
    mouse_pos_screen = pygame.mouse.get_pos()
    mouse_pos_world = camera.screen_to_world(mouse_pos_screen)

    # init debug felter hvis de ikke finnes
    if not hasattr(player, "attack_timer"):
        player.attack_timer = None
    if not hasattr(player, "debug_attack_rect"):
        player.debug_attack_rect = None
    if not hasattr(player, "debug_attack_until"):
        player.debug_attack_until = 0

    # --- bevegelse ---
    old_x, old_y = player.rect.x, player.rect.y
    if keys[pygame.K_w]:
        player.rect.y -= player.speed
        if _collides(player, obstacles): player.rect.y = old_y
    if keys[pygame.K_s]:
        player.rect.y += player.speed
        if _collides(player, obstacles): player.rect.y = old_y
    if keys[pygame.K_a]:
        player.rect.x -= player.speed
        if _collides(player, obstacles): player.rect.x = old_x
    if keys[pygame.K_d]:
        player.rect.x += player.speed
        if _collides(player, obstacles): player.rect.x = old_x

    # --- cooldown slutt? ---
    if now > player.attack_cooldown:
        player.playerAttack = False

    # --- skyting ---
    mouse_buttons = pygame.mouse.get_pressed()

    if mouse_buttons[0] and now >= player.attack_cooldown:
        direction = pygame.math.Vector2(
            mouse_pos_world[0] - player.rect.centerx,
            mouse_pos_world[1] - player.rect.centery
        )
    
        if direction.length_squared() > 0:
            proj = Projectile(player.rect.center, direction)
            world.projectiles.append(proj)

            player.attack_cooldown = now + constants.PLAYER_ATTACK_COOLDOWN

    # død?
    if player.health <= 0:
        player.alive = False

def _collides(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False
