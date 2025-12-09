from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ClickWorld:
    x: float
    y: float

@dataclass(frozen=True)
class ClickUI:
    ui_id: str
    x: float
    y: float

@dataclass(frozen=True)
class Scroll:
    delta: float

