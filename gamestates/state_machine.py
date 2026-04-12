from __future__ import annotations

import pygame

from .basestate import BaseState, State
from .boss_reward import BossRewardState
from .floor_transition import FloorTransitionState
from .main_menu import MainMenuState
from .char_select import CharacterSelectState
from .playing import PlayingState
from .paused import PausedState
from .game_over import GameOverState
from .room_reward import RoomRewardState


class StateMachine:

    def __init__(self, screen: pygame.Surface):
        self.screen             = screen
        self.running            = True
        self.selected_character = 0   # index into character_select.CHARACTERS

        # Game objects — set by start_game()
        self.world        = None
        self.player       = None
        self.room_manager = None
        self.hud          = None
        self.camera       = None

        self._states: dict[State, BaseState] = {}
        self._current: State = State.MAIN_MENU

        # Menu states are safe to build immediately
        self._states[State.MAIN_MENU]        = MainMenuState(self)
        self._states[State.CHARACTER_SELECT] = CharacterSelectState(self)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        state = self._states.get(self._current)
        if state:
            state.handle_event(event)

    def update(self, dt: int):
        state = self._states.get(self._current)
        if state:
            state.update(dt)

    def draw(self):
        state = self._states.get(self._current)
        if state:
            state.draw(self.screen)

    def transition(self, new_state: State):
        self._current = new_state
        state = self._states.get(new_state)
        if state:
            state.on_enter()

    def start_game(self):

        from core.world          import World
        from entities.player     import Player
        from core.camera         import Camera
        from rooms.room_manager  import RoomManager
        from core                  import HUD

        self.world        = World()
        self.camera       = Camera(self.screen.get_width(), self.screen.get_height())
        self.hud          = HUD()
        self.player       = Player(selected_character=self.selected_character, hud=self.hud)
        self.room_manager = RoomManager(self.world, self.player, self.camera)

        playing          = PlayingState(self)
        game_over        = GameOverState(self)
        paused           = PausedState(self, playing)
        boss_reward      = BossRewardState(self)
        room_reward      = RoomRewardState(self)
        floor_transition = FloorTransitionState(self)

        self._states[State.PLAYING]          = playing
        self._states[State.GAME_OVER]        = game_over
        self._states[State.PAUSED]           = paused
        self._states[State.BOSS_REWARD]      = boss_reward
        self._states[State.ROOM_REWARD]      = room_reward
        self._states[State.FLOOR_TRANSITION] = floor_transition

        self.transition(State.PLAYING)