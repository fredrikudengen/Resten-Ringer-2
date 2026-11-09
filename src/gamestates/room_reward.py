from __future__ import annotations

import random

from src.gamestates.basestate import State
from src.gamestates.reward_base import RewardState


class RoomRewardState(RewardState):
    """Etter et belønningsrom: ett tilfeldig tilbud, som kan avslås med ESC."""

    next_state = State.PLAYING
    can_skip   = True

    def _choose_offers(self, offers: list[dict]) -> list[dict]:
        return [random.choice(offers)]
