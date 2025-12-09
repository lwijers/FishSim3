# engine/game/components/velocity.py
from dataclasses import dataclass


@dataclass
class Velocity:
    vx: float
    vy: float
