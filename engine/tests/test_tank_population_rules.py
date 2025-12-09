# engine/tests/test_tank_population_rules.py
from __future__ import annotations

import random

from engine.ecs import World
from engine.game.components import Fish, InTank, Tank
from engine.game.factories import load_species_config
from engine.game.rules import (
    count_fish_in_tank,
    can_spawn_fish_in_tank,
    spawn_fish_in_tank_if_allowed,
)


def _add_fish_in_tank(world: World, tank_eid, species_id: str = "debug_fish") -> int:
    """
    Helper: add a bare Fish + InTank to the world without using create_fish.
    We don't care about position/velocity/sprite for population counting.
    """
    eid = world.create_entity()
    world.add_component(eid, Fish(species_id=species_id))
    world.add_component(eid, InTank(tank=tank_eid))
    return eid


def test_count_fish_in_tank_counts_only_that_tank() -> None:
    world = World()

    # Two tanks in the same world
    tank1 = world.create_entity()
    world.add_component(tank1, Tank(tank_id="tank_1", max_fish=10))
    tank2 = world.create_entity()
    world.add_component(tank2, Tank(tank_id="tank_2", max_fish=10))

    # Add 2 fish in tank1, 1 fish in tank2
    _add_fish_in_tank(world, tank1)
    _add_fish_in_tank(world, tank1)
    _add_fish_in_tank(world, tank2)

    assert count_fish_in_tank(world, tank1) == 2
    assert count_fish_in_tank(world, tank2) == 1


def test_can_spawn_fish_in_tank_respects_max_fish() -> None:
    world = World()
    tank = world.create_entity()
    world.add_component(tank, Tank(tank_id="cap_test", max_fish=2))

    # Initially empty -> OK
    assert can_spawn_fish_in_tank(world, tank) is True

    # Add 2 fish -> cap reached
    _add_fish_in_tank(world, tank)
    _add_fish_in_tank(world, tank)

    assert count_fish_in_tank(world, tank) == 2
    assert can_spawn_fish_in_tank(world, tank) is False


def test_can_spawn_fish_in_tank_no_tank_component_means_no_cap() -> None:
    world = World()
    # Create an entity but DO NOT add Tank() component
    pseudo_tank = world.create_entity()

    # Spec says: if no Tank component -> treat as "no limit"
    assert can_spawn_fish_in_tank(world, pseudo_tank) is True


def test_spawn_fish_in_tank_if_allowed_spawns_and_links_to_tank() -> None:
    """
    When under the cap, spawn_fish_in_tank_if_allowed should:
      - return a new entity id
      - add that fish to the requested tank (InTank.tank == tank_eid)
      - increase the population count for that tank
    """
    world = World()
    tank = world.create_entity()
    world.add_component(tank, Tank(tank_id="tank_spawn", max_fish=2))

    species_cfg = load_species_config()
    rng = random.Random(123)

    # First spawn -> allowed
    fish_eid = spawn_fish_in_tank_if_allowed(
        world,
        tank_eid=tank,
        species_cfg=species_cfg,
        species_id="debug_fish",
        x=100.0,
        y=100.0,
        rng=rng,
    )
    assert fish_eid is not None
    assert count_fish_in_tank(world, tank) == 1

    # Check that InTank points to the right tank
    in_tank_store = world.get_components(InTank)
    in_tank = in_tank_store[fish_eid]
    assert in_tank.tank == tank


def test_spawn_fish_in_tank_if_allowed_blocks_when_full() -> None:
    """
    Once the tank has reached max_fish, further spawns should return None
    and not increase the population count.
    """
    world = World()
    tank = world.create_entity()
    world.add_component(tank, Tank(tank_id="tank_full", max_fish=1))

    species_cfg = load_species_config()
    rng = random.Random(999)

    # First spawn -> allowed
    first = spawn_fish_in_tank_if_allowed(
        world,
        tank_eid=tank,
        species_cfg=species_cfg,
        species_id="debug_fish",
        x=50.0,
        y=50.0,
        rng=rng,
    )
    assert first is not None
    assert count_fish_in_tank(world, tank) == 1

    # Second spawn -> blocked
    second = spawn_fish_in_tank_if_allowed(
        world,
        tank_eid=tank,
        species_cfg=species_cfg,
        species_id="debug_fish",
        x=60.0,
        y=60.0,
        rng=rng,
    )
    assert second is None
    assert count_fish_in_tank(world, tank) == 1
