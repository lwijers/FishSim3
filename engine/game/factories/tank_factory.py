# engine/game/factories/tank_factory.py
from __future__ import annotations

from typing import Any, Dict

from engine.ecs import World, EntityId
from engine.game.components.tank import Tank
from engine.game.components.tank_bounds import TankBounds
from engine.game.data.jsonio import load_json


TankConfig = Dict[str, Any]


def load_tank_config() -> TankConfig:
    """
    Load tanks.json and return the whole structure.

    Expected structure:

        {
          "_version": 1,
          "tanks": {
            "tank_1": {
              "max_fish": 20,
              "bounds": [0.0, 0.0, 1280.0, 720.0],
              "debug_spawn": {
                "count": 8,
                "margin": 50.0
              }
            }
          }
        }
    """
    raw = load_json("tanks.json")
    return raw


def create_tank(
    world: World,
    tank_id: str,
    max_fish: int,
    x: float,
    y: float,
    width: float,
    height: float,
) -> EntityId:
    """
    Create a tank entity with:
      - Tank(tank_id, max_fish)
      - TankBounds(x, y, width, height)

    MovementSystem uses TankBounds to keep fish inside their tank.
    """
    eid = world.create_entity()
    world.add_component(eid, Tank(tank_id=tank_id, max_fish=max_fish))
    world.add_component(eid, TankBounds(x=x, y=y, width=width, height=height))
    return eid
