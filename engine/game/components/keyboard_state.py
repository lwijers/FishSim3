from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KeyboardState:
    keys: Dict[str, bool] = field(default_factory=dict)
