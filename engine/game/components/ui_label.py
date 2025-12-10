from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UILabel:
    text: str
    text_key: str | None = None
