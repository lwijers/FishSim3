# engine/app/constants.py
from __future__ import annotations
from typing import Tuple

"""
Non-user-tweakable engine constants.

Everything a player might reasonably tweak lives in JSON data files under
engine/game/data. These constants are for engine behaviour, tests, and
safe fallbacks.
"""

# ----------------------------------------------------------------------
# Engine timing
# ----------------------------------------------------------------------
# Frame rate cap for the main loop (PygameApp).
FPS: int = 60

# ----------------------------------------------------------------------
# RNG seeding for deterministic behaviour
# ----------------------------------------------------------------------
RNG_ROOT_SEED: int = 42
RNG_MAX_INT: int = 2**31 - 1

# ----------------------------------------------------------------------
# Window / screen defaults
# ----------------------------------------------------------------------
# Used when settings.json is missing/incomplete.
FALLBACK_SCREEN_SIZE: Tuple[int, int] = (800, 600)
DEFAULT_WINDOW_SIZE: Tuple[int, int] = (1280, 720)
DEFAULT_WINDOW_TITLE: str = "FishSim3 MVP"

# ----------------------------------------------------------------------
# Gameplay defaults (not exposed as user settings… yet)
# ----------------------------------------------------------------------
FSM_IDLE_DURATION: float = 1.0
FSM_CRUISE_DURATION: float = 2.0
FSM_DEFAULT_CRUISE_SPEED: float = 80.0

# Default tank id used at startup if no explicit choice is configured.
DEFAULT_TANK_ID: str = "tank_1"

# ----------------------------------------------------------------------
# UI defaults
# ----------------------------------------------------------------------
# Used only if ui.json is missing or broken.
DEFAULT_BG_COLOR: Tuple[int, int, int] = (30, 40, 90)
