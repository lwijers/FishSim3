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


def load_debug_panels_config() -> Dict[str, Any]:
    """
    Debug panel toggles/keys and related flags.
    """
    return load_json("debug_panels.json")


def load_pellet_config() -> Dict[str, Any]:
    """
    Pellet defaults: size, color, sprite_id.
    """
    return load_json("pellets.json")


def load_fsm_config() -> Dict[str, Any]:
    """
    Fish FSM config: start state weights, idle/cruise duration ranges, cruise placement tuning.
    """
    return load_json("fsm.json")


def load_falling_config() -> Dict[str, Any]:
    """
    Global defaults for falling behaviour (gravity, terminal velocity).
    """
    return load_json("falling.json")


def load_movement_config() -> Dict[str, Any]:
    """
    Movement tuning (max acceleration, max speed).
    """
    return load_json("movement.json")
