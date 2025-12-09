# engine/game/rules/population.py
from __future__ import annotations
from typing import Optional
from engine.ecs import World, EntityId
from engine.game.components.fish import Fish
from engine.game.components.in_tank import InTank
from engine.game.components.tank import Tank
from engine.game.factories import create_fish

def count_fish_in_tank(world: World, tank_eid: EntityId) -> int:
    """
    Count how many Fish are in a given tank (by InTank.tank).
    """
    count = 0
    for eid, fish, in_tank in world.view(Fish, InTank):
        if in_tank.tank == tank_eid:
            count += 1
    return count

def can_spawn_fish_in_tank(world: World, tank_eid: EntityId) -> bool:
    """
    Check if the given tank is under its max_fish limit.
    If the tank has no Tank component (shouldn't happen in normal play),
    we treat it as 'no limit' for now.
    """
    tank_store = world.get_components(Tank)
    tank = tank_store.get(tank_eid)
    if tank is None:
        # No tank data -> no cap.
        return True
    current = count_fish_in_tank(world, tank_eid)
    return current < tank.max_fish

def spawn_fish_in_tank_if_allowed(
    world: World,
    tank_eid: EntityId,
    species_cfg,
    species_id: str,
    x: float,
    y: float,
    rng,
) -> Optional[EntityId]:
    """
    Central entry point for spawning fish *per tank*.

    - Checks can_spawn_fish_in_tank.
    - If allowed: creates fish and attaches InTank(tank_eid).
    - If not allowed: returns None (caller can decide what to do).
    """
    if not can_spawn_fish_in_tank(world, tank_eid):
        return None

    fish_eid = create_fish(world, species_cfg, species_id, x, y, rng)

    # Attach tank link
    from engine.game.components.in_tank import InTank  # local import to avoid cycles
    world.add_component(fish_eid, InTank(tank=tank_eid))
    return fish_eid
