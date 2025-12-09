# engine/game/systems/__init__.py
from .movement_system import MovementSystem
from .rect_render_system import RectRenderSystem
from .fish_fsm_system import FishFSMSystem
from .sprite_render_system import SpriteRenderSystem
from .placement_system import PlacementSystem
from .falling_system import FallingSystem
from .ui_button_system import UIButtonSystem

__all__ = [
    "MovementSystem",
    "RectRenderSystem",
    "FishFSMSystem",
    "SpriteRenderSystem",
    "PlacementSystem",
    "FallingSystem",
    "UIButtonSystem",
]
