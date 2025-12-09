# engine/game/fsm/__init__.py
"""
Finite State Machine (FSM) helpers for the fish game.
"""

from .base_state import FishState
from .idle_state import IdleState
from .cruise_state import CruiseState

__all__ = ["FishState", "IdleState", "CruiseState"]
