# engine/game/rules/__init__.py
from .population import (
    count_fish_in_tank,
    can_spawn_fish_in_tank,
    spawn_fish_in_tank_if_allowed,
)

__all__ = ["count_fish_in_tank", "can_spawn_fish_in_tank", "spawn_fish_in_tank_if_allowed"]
