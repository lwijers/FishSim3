from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UIButton:
    tool_id: str | None = None
    active: bool = False
    hover: bool = False
    exclusive_group: str | None = None
    deactivate_on_right_click: bool = True
