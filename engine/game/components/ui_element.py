from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UIElement:
    width: float
    height: float
    style: str | None = None
    element_id: str | None = None
