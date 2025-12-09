from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Falling:
    """
    Reusable falling behaviour parameters.
    - gravity: optional override for downward acceleration (positive = down)
    - terminal_velocity: optional clamp for downward speed
    - wobble_amplitude: horizontal sway amplitude (units/sec)
    - wobble_frequency: cycles per second for the sway
    - wobble_phase: initial phase offset (radians)
    - wobble_time: accumulated time for the sine wave
    - stop_on_floor: if True, zero velocity when hitting floor and mark grounded
    - grounded: runtime flag set when the entity has landed
    """
    gravity: float | None = None
    terminal_velocity: float | None = None
    wobble_amplitude: float | None = None
    wobble_frequency: float | None = None
    wobble_phase: float | None = None
    wobble_time: float = 0.0
    stop_on_floor: bool = True
    grounded: bool = False
