from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ClickWorld:
    x: float
    y: float
    button: int = 1


@dataclass(frozen=True)
class PointerMove:
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

