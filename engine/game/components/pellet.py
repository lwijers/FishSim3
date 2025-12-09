from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Pellet:
    """Marker for pellets; rendering uses RectSprite/SpriteRef."""
    size: float = 12.0
