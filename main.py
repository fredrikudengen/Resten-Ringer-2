import pygame
import constants
from entities import Player
from components import Camera
from core import player_input
from core import World
from rooms import RoomManager
from ui import HUD

pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

player = Player(screen_width // 2, screen_height // 2)
camera = Camera(screen_width, screen_height)

world = World()
room_manager = RoomManager(world, player, camera)

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False

    # update
    player.update_powerups()
    player_input(player, world.obstacles, world, camera)
    camera.update(player.rect)

    dt_ms = clock.get_time()
    world.update(dt_ms, player)
    
    if player.health <= 0:
        run = False

    room_manager.update()

    hud = HUD()
    player._hud = hud

    # draw
    screen.fill(constants.BLACK)
    world.draw(screen, camera)
    room_manager.draw(screen)  
    player.draw(screen, camera)
    hud.draw(screen, player)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
