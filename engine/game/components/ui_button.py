from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UIButton:
    tool_id: str
    active: bool = False
    hover: bool = False
