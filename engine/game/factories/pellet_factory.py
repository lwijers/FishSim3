from __future__ import annotations
import random
from typing import Mapping, Any, Iterable

from engine.ecs import World, EntityId
from engine.ecs.commands import CreateEntityCmd
from engine.game.components import Position, RectSprite, SpriteRef, InTank, Velocity
from engine.game.components.pellet import Pellet
from engine.game.components.falling import Falling

def create_pellet_cmd(
    x: float,
    y: float,
    tank_eid: EntityId,
    pellet_cfg: Mapping[str, Any] | None = None,
    rng: random.Random | None = None,
) -> CreateEntityCmd:
    """
    Build a queued entity command for a pellet at logical coords (x, y).

    pellet_cfg keys (all optional):
      - size: float
      - color: [r, g, b]
      - sprite_id: str
    """
    def _pick(cfg: Mapping[str, Any], key: str, default=None):
        range_key = f"{key}_range"
        if range_key in cfg:
            lo, hi = cfg[range_key]
            return (rng or random).uniform(float(lo), float(hi))
        if key in cfg:
            return cfg[key]
        return default

    cfg = pellet_cfg or {}
    size = float(cfg.get("size", 12.0))
    color_val: Iterable[Any] = cfg.get("color", (0, 0, 0))
    color_tuple = tuple(color_val)
    sprite_id = cfg.get("sprite_id")
    fall_cfg = cfg.get("falling", {})
    falling = Falling(
        gravity=fall_cfg.get("gravity"),
        terminal_velocity=fall_cfg.get("terminal_velocity"),
        wobble_amplitude=_pick(fall_cfg, "wobble_amplitude"),
        wobble_frequency=_pick(fall_cfg, "wobble_frequency"),
        wobble_phase=_pick(fall_cfg, "wobble_phase", 0.0),
        wobble_time=float(_pick(fall_cfg, "wobble_time", 0.0)),
        stop_on_floor=bool(fall_cfg.get("stop_on_floor", True)),
    )

    pellet = Pellet(size=size)
    components = {
        Position: Position(x=x, y=y),
        Velocity: Velocity(vx=0.0, vy=0.0),
        RectSprite: RectSprite(width=size, height=size, color=color_tuple),
        InTank: InTank(tank=tank_eid),
        Pellet: pellet,
        Falling: falling,
    }
    if sprite_id:
        components[SpriteRef] = SpriteRef(sprite_id=sprite_id, width=size, height=size)
    return CreateEntityCmd(components)
