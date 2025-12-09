# engine/game/data/configs.py
from __future__ import annotations
from typing import Any, Dict
from .jsonio import load_json


def load_settings_config() -> Dict[str, Any]:
    """
    User-tweakable runtime settings (window size, logical size, etc.).
    """
    return load_json("settings.json")


def load_ui_config() -> Dict[str, Any]:
    """
    UI theme configuration: colors, fonts, etc.
    """
    return load_json("ui.json")


def load_pellet_config() -> Dict[str, Any]:
    """
    Pellet defaults: size, color, sprite_id.
    """
    return load_json("pellets.json")


def load_falling_config() -> Dict[str, Any]:
    """
    Global defaults for falling behaviour (gravity, terminal velocity).
    """
    return load_json("falling.json")
