import math

import pygame

def player_input(player, obstacles, camera):
    keys = pygame.key.get_pressed()
    mouse_pos_screen = pygame.mouse.get_pos()
    mouse_pos_world = camera.screen_to_world(*mouse_pos_screen)
    player.is_moving = False

    dx = (keys[pygame.K_d] - keys[pygame.K_a])
    dy = (keys[pygame.K_s] - keys[pygame.K_w])

    if dx != 0 or dy != 0:
        length = math.sqrt(dx * dx + dy * dy)
        player.velocity.x = dx / length * player.speed
        player.velocity.y = dy / length * player.speed
    else:
        player.velocity *= 0.80
        if player.velocity.length() < 0.5:
            player.velocity = pygame.math.Vector2(0, 0)

    player.is_moving = player.velocity.length() > 0.5

    if player.velocity.length() > 0:
        old_x = player.rect.x
        player.rect.x += round(player.velocity.x)
        if _collides(player, obstacles):
            player.rect.x = old_x
            player.velocity.x = 0

        old_y = player.rect.y
        player.rect.y += round(player.velocity.y)
        if _collides(player, obstacles):
            player.rect.y = old_y
            player.velocity.y = 0

    # --- dash ---
    if keys[pygame.K_SPACE]:
        dash_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]: dash_dir.y -= 1
        if keys[pygame.K_s]: dash_dir.y += 1
        if keys[pygame.K_a]: dash_dir.x -= 1
        if keys[pygame.K_d]: dash_dir.x += 1

        if dash_dir.length_squared() == 0:
            dash_dir = pygame.math.Vector2(
                mouse_pos_world[0] - player.rect.centerx,
                mouse_pos_world[1] - player.rect.centery
            )
        player.start_dash(dash_dir)

    player.update_knockback(obstacles)
    player.update_dash(obstacles)
    player.update_powerups()

    player.sync_pos_from_rect()

def _collides(player, obstacles):
    for obs in obstacles:
        if player.rect.colliderect(obs):
            return True
    return False