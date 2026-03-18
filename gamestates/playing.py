from __future__ import annotations

import pygame

from .basestate import BaseState, State
from core import constants


class PlayingState(BaseState):
    """
    Delegates update/draw to the existing game objects.
    Requires sm.world, sm.player, sm.room_manager, sm.hud, sm.camera
    to be set up by StateMachine.start_game() before entering this state.
    """

    def __init__(self, sm):
        self._sm = sm

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._sm.transition(State.PAUSED)

    def update(self, dt: int):
        from controller import player_input
        sm = self._sm

        player_input(sm.player, sm.world.obstacles, sm.world, sm.camera)
        sm.camera.update(sm.player.rect)
        sm.world.update(dt, sm.player)
        sm.room_manager.update(sm.player)

        if not sm.player.alive:
            self._sm.transition(State.GAME_OVER)

    def draw(self, surface: pygame.Surface):
        sm = self._sm
        surface.fill(constants.TILE_FLOOR_COLOR)
        sm.world.draw(surface, sm.camera)
        sm.room_manager.draw(surface)
        sm.player.draw(surface, sm.camera)
        sm.hud.draw(surface, sm.player)