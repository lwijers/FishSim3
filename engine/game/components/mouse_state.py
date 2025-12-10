from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MouseState:
    x: float = 0.0
    y: float = 0.0
    buttons: Dict[int, bool] = field(default_factory=dict)
