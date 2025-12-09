from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Falling:
    """
    Reusable falling behaviour parameters.
    - gravity: optional override for downward acceleration (positive = down)
    - terminal_velocity: optional clamp for downward speed
    - stop_on_floor: if True, zero velocity when hitting floor and mark grounded
    - grounded: runtime flag set when the entity has landed
    """
    gravity: float | None = None
    terminal_velocity: float | None = None
    stop_on_floor: bool = True
    grounded: bool = False
