# engine/game/factories/fish_factory.py
from __future__ import annotations

import random
from typing import Any, Dict

from engine.ecs import World, EntityId
from engine.game.components import (
    Position,
    Velocity,
    RectSprite,
    Fish,
    Brain,
    MovementIntent,
)
from engine.game.data.jsonio import load_json

SpeciesConfig = Dict[str, Any]
SpeciesConfigMap = Dict[str, SpeciesConfig]


def load_species_config() -> SpeciesConfigMap:
    """
    Load species.json and return the 'species' dict.
    Structure of the json is:
      { "_version": 1, "species": { "debug_fish": { ... } } }
    """
    raw = load_json("species.json")
    species = raw.get("species", {})
    return species


def create_fish(
    world: World,
    species_cfg: SpeciesConfigMap,
    species_id: str,
    x: float,
    y: float,
    rng: random.Random,
) -> EntityId:
    """
    Create a fish entity from species config at a given position.

    Components:
      - Position
      - Velocity (starts at 0; FSM + MovementIntent will drive it)
      - RectSprite (width/height/color from config)
      - Fish (species_id)
      - Brain (FSM state)
      - MovementIntent (AI output)
    """
    spec = species_cfg[species_id]

    width = float(spec["width"])
    height = float(spec["height"])
    color = tuple(spec["color"])  # [r, g, b] -> (r, g, b)

    eid = world.create_entity()
    world.add_component(eid, Position(x=x, y=y))
    # Start with zero velocity; AI will fill in MovementIntent.
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=width, height=height, color=color))
    world.add_component(eid, Fish(species_id=species_id))
    world.add_component(eid, Brain())
    world.add_component(eid, MovementIntent())

    return eid
