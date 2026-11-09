from __future__ import annotations

from src.gamestates.basestate import State
from src.gamestates.reward_base import RewardState


class BossRewardState(RewardState):
    """Etter bossen: velg ett av tre tilbud (våpen, oppgradering, relic), så neste etasje."""

    next_state = State.FLOOR_TRANSITION
