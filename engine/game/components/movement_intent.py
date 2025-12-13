# engine/game/components/movement_intent.py
from dataclasses import dataclass


@dataclass
class MovementIntent:
    """
    Desired movement for this entity in logical space.

    AI / FSM systems write this.
    MovementSystem reads it and turns it into actual Velocity.
    """
    target_vx: float = 0.0
    target_vy: float = 0.0
    # Optional debug-only target position (logical space) for visualization.
    debug_target: tuple[float, float] | None = None
