from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Bobbing:
    amplitude: float
    frequency: float
    phase: float = 0.0
    t: float = 0.0
