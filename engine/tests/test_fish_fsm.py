# engine/tests/test_fish_fsm.py
from __future__ import annotations

import math
import random

from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Fish, Brain, MovementIntent
from engine.game.systems import FishFSMSystem


def _make_world_and_fsm() -> tuple[World, ResourceStore, FishFSMSystem]:
    """
    Helper: create a World + ResourceStore + FishFSMSystem
    with a deterministic rng_ai.
    """
    world = World()
    resources = ResourceStore()

    # Deterministic RNG for FSM decisions
    rng_ai = random.Random(123)
    resources.set("rng_ai", rng_ai)

    fsm_sys = FishFSMSystem(resources)
    return world, resources, fsm_sys


def test_fish_fsm_idle_to_cruise_to_idle() -> None:
    """
    A fish should:
      - start in 'idle' with zero intent
      - after IDLE_DURATION, switch to 'cruise' with non-zero intent
      - after CRUISE_DURATION, switch back to 'idle' with zero intent again
    """
    world, resources, fsm_sys = _make_world_and_fsm()

    eid = world.create_entity()
    world.add_component(eid, Fish(species_id="debug_fish"))
    brain = Brain()
    intent = MovementIntent()
    world.add_component(eid, brain)
    world.add_component(eid, intent)

    # Before any update
    assert brain.state == "idle"
    assert brain.initialized is False
    assert intent.target_vx == 0.0
    assert intent.target_vy == 0.0

    # After exactly one idle duration: should have transitioned to cruise
    fsm_sys.update(world, dt=FishFSMSystem.IDLE_DURATION)

    assert brain.state == "cruise"
    assert brain.initialized is True
    # Entering cruise resets time_in_state
    assert brain.time_in_state == 0.0
    # Cruise should have non-zero intent
    assert (intent.target_vx != 0.0) or (intent.target_vy != 0.0)

    # After cruise duration: should be back in idle with zero intent
    fsm_sys.update(world, dt=FishFSMSystem.CRUISE_DURATION)

    assert brain.state == "idle"
    assert intent.target_vx == 0.0
    assert intent.target_vy == 0.0


def test_multiple_fish_share_fsm_but_have_independent_brains() -> None:
    """
    Two fish with brains should both be updated by the FSM system and keep
    their own state / timers.
    """
    world, resources, fsm_sys = _make_world_and_fsm()

    e1 = world.create_entity()
    e2 = world.create_entity()
    world.add_component(e1, Fish(species_id="debug_fish"))
    world.add_component(e2, Fish(species_id="debug_fish"))

    b1 = Brain()
    b2 = Brain()
    i1 = MovementIntent()
    i2 = MovementIntent()
    world.add_component(e1, b1)
    world.add_component(e1, i1)
    world.add_component(e2, b2)
    world.add_component(e2, i2)

    # Run one idle duration (both should leave idle → cruise)
    fsm_sys.update(world, dt=FishFSMSystem.IDLE_DURATION)

    assert b1.state == "cruise"
    assert b2.state == "cruise"

    # Intent should be non-zero for both (but not necessarily equal)
    assert (i1.target_vx != 0.0) or (i1.target_vy != 0.0)
    assert (i2.target_vx != 0.0) or (i2.target_vy != 0.0)

    # Advance cruise and ensure both go back to idle separately
    fsm_sys.update(world, dt=FishFSMSystem.CRUISE_DURATION)

    assert b1.state == "idle"
    assert b2.state == "idle"
    assert i1.target_vx == 0.0 and i1.target_vy == 0.0
    assert i2.target_vx == 0.0 and i2.target_vy == 0.0


def test_cruise_uses_species_speed_range() -> None:
    """
    CruiseState should respect species_config['speed_range'] when present.

    We:
      - provide a custom species_config with a tight [min, max] range
      - let the FSM transition idle → cruise
      - measure the resulting MovementIntent speed
      - assert it falls within the configured range
    """
    world = World()
    resources = ResourceStore()

    # Deterministic RNG for reproducible direction/speed
    rng_ai = random.Random(999)
    resources.set("rng_ai", rng_ai)

    # Custom species config with a narrow speed range
    speed_min = 10.0
    speed_max = 15.0
    species_cfg = {
        "debug_fish": {
            "speed_range": [speed_min, speed_max],
        }
    }
    resources.set("species_config", species_cfg)

    fsm_sys = FishFSMSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Fish(species_id="debug_fish"))
    brain = Brain()
    intent = MovementIntent()
    world.add_component(eid, brain)
    world.add_component(eid, intent)

    # Trigger first transition: idle → cruise
    fsm_sys.update(world, dt=FishFSMSystem.IDLE_DURATION)

    assert brain.state == "cruise"

    # Compute resulting speed from intent vector
    speed = math.hypot(intent.target_vx, intent.target_vy)

    assert speed_min <= speed <= speed_max
