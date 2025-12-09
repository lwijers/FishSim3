from __future__ import annotations
from typing import Dict, Any

from engine.ecs import World, EntityId
from engine.ecs.commands import CreateEntityCmd
from engine.game.components import Position, RectSprite, InTank
from engine.game.components.pellet import Pellet

DEFAULT_PELLET_SIZE = 12.0
DEFAULT_PELLET_COLOR = (210, 180, 90)

def create_pellet_cmd(
    x: float,
    y: float,
    tank_eid: EntityId,
    size: float = DEFAULT_PELLET_SIZE,
    color=DEFAULT_PELLET_COLOR,
) -> CreateEntityCmd:
    """Build a queued entity command for a pellet at logical coords (x, y)."""
    pellet = Pellet(size=size)
    return CreateEntityCmd({
        Position: Position(x=x, y=y),
        RectSprite: RectSprite(width=size, height=size, color=color),
        InTank: InTank(tank=tank_eid),
        Pellet: pellet,
    })
