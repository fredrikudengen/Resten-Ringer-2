import random
from types import SimpleNamespace

import pygame

from components.gun import Pistol
from gamestates.basestate import State
from gamestates.boss_reward import BossRewardState
from gamestates.reward_base import STAT_UPGRADES
from gamestates.room_reward import RoomRewardState


class _FakeSM:
    def __init__(self):
        self.player = SimpleNamespace(gun=Pistol(), relics=[])
        self.screen = pygame.Surface((1280, 720))
        self.transitions = []

    def transition(self, state):
        # Navnet, ikke enumen: koden importerer State som src.gamestates.basestate,
        # testene som gamestates.basestate, og da er det to ulike klasser
        self.transitions.append(state.name)


def _ammo_upgrade():
    return next(u for u in STAT_UPGRADES if "Max Ammo" in u["label"])


def _click(state, idx):
    rect = list(state._card_layout(*state._sm.screen.get_size()))[idx][0]
    state.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))


def _esc(state):
    state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))


def test_ammo_upgrade_matches_its_label():
    player = SimpleNamespace(gun=SimpleNamespace(max_ammo=12))
    _ammo_upgrade()["apply"](player)
    assert _ammo_upgrade()["label"] == "+30% Max Ammo"
    assert player.gun.max_ammo == 16


def test_ammo_upgrade_keeps_infinite_ammo_infinite():
    # max_ammo = -1 betyr uendelig (standard i Gun). "+2" ville gjort det om til 1 skudd
    player = SimpleNamespace(gun=SimpleNamespace(max_ammo=-1))
    _ammo_upgrade()["apply"](player)
    assert player.gun.max_ammo < 0


def test_boss_reward_offers_one_of_each_type_and_goes_to_next_floor():
    random.seed(0)
    state = BossRewardState(_FakeSM())
    state.on_enter()
    assert [o["type"] for o in state._offers] == ["VÅPEN", "UPGRADE", "RELIC"]

    _esc(state)
    assert state._sm.transitions == []  # bossbelønningen kan ikke avslås

    _click(state, 1)
    assert state._sm.transitions == [State.FLOOR_TRANSITION.name]


def test_room_reward_offers_one_card_that_can_be_skipped():
    random.seed(0)
    state = RoomRewardState(_FakeSM())
    state.on_enter()
    assert len(state._offers) == 1

    _esc(state)
    assert state._sm.transitions == [State.PLAYING.name]


def test_clicking_a_card_applies_it():
    state = RoomRewardState(_FakeSM())
    applied = []
    state._offers = [{"type": "UPGRADE", "label": "x", "desc": "", "color": (0, 0, 0),
                      "apply": lambda p: applied.append(p)}]
    _click(state, 0)
    assert applied == [state._sm.player]
    assert state._sm.transitions == [State.PLAYING.name]
