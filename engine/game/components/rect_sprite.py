# engine/game/components/rect_sprite.py
from dataclasses import dataclass
from typing import Tuple

Color = Tuple[int, int, int]


@dataclass
class RectSprite:
    """
    Very simple sprite definition for MVP:
    - width, height in pixels
    - solid fill color (RGB)
    """
    width: float
    height: float
    color: Color
