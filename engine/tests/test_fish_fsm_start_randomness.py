from __future__ import annotations
import random

from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Fish, Brain, MovementIntent
from engine.game.systems import FishFSMSystem


def test_fish_fsm_random_start_state_respects_weights() -> None:
    resources = ResourceStore()
    resources.set("fsm_config", {
        "start_state_weights": {"idle": 1.0, "cruise": 0.0},
        "idle_duration_range": [1.0, 1.0],
        "cruise_duration_range": [2.0, 2.0],
    })
    rng = random.Random(123)
    resources.set("rng_ai", rng)

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Fish(species_id="debug_fish"))
    world.add_component(eid, Brain())
    world.add_component(eid, MovementIntent())

    fsm_sys = FishFSMSystem(resources)
    fsm_sys.update(world, dt=0.0)

    _, brain = next(world.view(Brain))
    assert brain.state == "idle"


def test_fish_fsm_random_start_state_cruise_possible() -> None:
    resources = ResourceStore()
    resources.set("fsm_config", {
        "start_state_weights": {"idle": 0.0, "cruise": 1.0},
        "idle_duration_range": [1.0, 1.0],
        "cruise_duration_range": [2.0, 2.0],
    })
    rng = random.Random(999)
    resources.set("rng_ai", rng)

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Fish(species_id="debug_fish"))
    world.add_component(eid, Brain())
    world.add_component(eid, MovementIntent())

    fsm_sys = FishFSMSystem(resources)
    fsm_sys.update(world, dt=0.0)

    _, brain = next(world.view(Brain))
    assert brain.state == "cruise"


def test_fish_fsm_duration_ranges() -> None:
    resources = ResourceStore()
    resources.set("fsm_config", {
        "start_state_weights": {"idle": 1.0, "cruise": 0.0},
        "idle_duration_range": [3.0, 3.0],
        "cruise_duration_range": [5.0, 5.0],
    })
    rng = random.Random(1)
    resources.set("rng_ai", rng)

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Fish(species_id="debug_fish"))
    world.add_component(eid, Brain())
    world.add_component(eid, MovementIntent())

    fsm_sys = FishFSMSystem(resources)
    fsm_sys.update(world, dt=0.0)

    _, brain = next(world.view(Brain))
    assert brain.state_duration == 3.0
