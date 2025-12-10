# engine/game/systems/__init__.py
from .movement_system import MovementSystem
from .rect_render_system import RectRenderSystem
from .fish_fsm_system import FishFSMSystem
from .sprite_render_system import SpriteRenderSystem
from .placement_system import PlacementSystem
from .falling_system import FallingSystem
from .ui_button_system import UIButtonSystem
from .keyboard_system import KeyboardSystem
from .mouse_system import MouseSystem
from .ui_label_system import UILabelSystem
from .debug_menu_system import DebugManagerSystem
from .fish_state_label_system import FishStateLabelSystem
from .movement_debug_system import MovementDebugSystem

__all__ = [
    "MovementSystem",
    "RectRenderSystem",
    "FishFSMSystem",
    "SpriteRenderSystem",
    "PlacementSystem",
    "FallingSystem",
    "UIButtonSystem",
    "KeyboardSystem",
    "MouseSystem",
    "UILabelSystem",
    "DebugManagerSystem",
    "FishStateLabelSystem",
    "MovementDebugSystem",
]
