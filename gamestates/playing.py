from __future__ import annotations

import pygame

from .basestate import BaseState, State
from core import constants
from controller import player_input

class PlayingState(BaseState):
    """
    Delegates update/draw to the existing game objects.
    Requires sm.world, sm.player, sm.room_manager, sm.hud, sm.camera
    to be set up by StateMachine.start_game() before entering this state.
    """

    def __init__(self, sm):
        self._sm = sm
        self._shoot_requested = False
        self._reload_requested = False
        self._mouse_held = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._sm.transition(State.PAUSED)
            if event.key == pygame.K_r:
                self._reload_requested = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._mouse_held = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._mouse_held = False

    def update(self, dt: int):
        sm = self._sm

        player_input(sm.player, sm.world.obstacles, sm.camera)
        sm.camera.update(sm.player.rect)
        sm.world.update(dt, sm.player)
        sm.room_manager.update(sm.player)

        if self._mouse_held or self._shoot_requested:
            mx, my = pygame.mouse.get_pos()
            world_mouse = sm.camera.screen_to_world(mx, my)
            bullets = sm.player.shoot(world_mouse)
            sm.world.add_bullets(bullets)
            self._shoot_requested = False

        if self._reload_requested:
            sm.player.gun.start_reload()
            self._reload_requested = False

        sm.player.gun.update_reload()

        for enemy in sm.world.enemies:
            if getattr(enemy, 'did_slam', False):
                sm.camera.shake(8, 400)
                enemy.did_slam = False

        if sm.room_manager.pending_boss_reward:
            sm.room_manager.pending_boss_reward = False
            sm.transition(State.BOSS_REWARD)
            return

        if not sm.player.alive:
            self._sm.transition(State.GAME_OVER)

    def draw(self, surface: pygame.Surface):
        sm = self._sm
        surface.fill(constants.TILE_FLOOR_COLOR)
        sm.world.draw(surface, sm.camera)
        sm.room_manager.draw(surface)
        sm.player.draw(surface, sm.camera)
        sm.hud.draw(surface, sm.player)