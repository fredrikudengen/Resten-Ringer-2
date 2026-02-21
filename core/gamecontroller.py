import pygame
import constants

from components import Projectile


def player_input(player, obstacles, world, camera):
    keys = pygame.key.get_pressed()
    now = pygame.time.get_ticks()
    mouse_pos_screen = pygame.mouse.get_pos()
    mouse_pos_world = camera.screen_to_world(mouse_pos_screen)

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

    # --- skyting ---
    if now > player.attack_cooldown:
        player.playerAttack = False
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

    # --- dash ---
    if keys[pygame.K_SPACE]:
        dash_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]: dash_dir.y -= 1
        if keys[pygame.K_s]: dash_dir.y += 1
        if keys[pygame.K_a]: dash_dir.x -= 1
        if keys[pygame.K_d]: dash_dir.x += 1

        # Hvis ingen retning dash mot musen
        if dash_dir.length_squared() == 0:
            dash_dir = pygame.math.Vector2(
                mouse_pos_world[0] - player.rect.centerx,
                mouse_pos_world[1] - player.rect.centery
            )
        player.start_dash(dash_dir)
    
    player.update_knockback(obstacles)
    player.update_dash(obstacles)
    player.update_powerups()
    
    if player.health <= 0:
        player.alive = False

    player.sync_pos_from_rect()

def _collides(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False
