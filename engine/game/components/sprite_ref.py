# engine/game/components/sprite_ref.py
from dataclasses import dataclass


@dataclass
class SpriteRef:
    """Reference to a sprite in the asset store.

    sprite_id:
        Key used by the Assets resource to look up an image.
    width, height:
        Logical size of the sprite (same units as Position.x/y).
    facing_left:
        If true, the sprite will be rendered flipped horizontally so it faces
        left. Movement logic can toggle this based on velocity.
    """
    sprite_id: str
    width: float
    height: float
    facing_left: bool = False
