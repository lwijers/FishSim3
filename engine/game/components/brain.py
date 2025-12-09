# engine/game/components/brain.py
from dataclasses import dataclass


@dataclass
class Brain:
    """
    FSM brain for a fish.

    Fields:
      - state: current state name ("idle", "cruise", ...)
      - time_in_state: seconds spent in current state
      - state_duration: planned duration of current state
      - initialized: whether on_enter has run at least once for the current state
    """
    state: str = "idle"
    time_in_state: float = 0.0
    state_duration: float = 0.0
    initialized: bool = False
