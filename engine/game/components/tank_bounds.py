# engine/game/components/tank_bounds.py
from dataclasses import dataclass


@dataclass
class TankBounds:
    """
    Rectangular area for a tank in *logical* game space (not pixels).
    Movement uses these bounds; rendering will scale logical space
    to the current screen size.
    """
    x: float
    y: float
    width: float
    height: float
