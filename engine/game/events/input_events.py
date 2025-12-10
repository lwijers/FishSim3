from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ClickWorld:
    x: float
    y: float
    button: int = 1


@dataclass(frozen=True)
class ClickUI:
    id: str | None = None
    x: float | None = None
    y: float | None = None


@dataclass(frozen=True)
class PointerMove:
    x: float
    y: float


@dataclass(frozen=True)
class KeyEvent:
    key: str
    pressed: bool


@dataclass(frozen=True)
class Scroll:
    delta: float
