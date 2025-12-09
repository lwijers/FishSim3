from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Position, Velocity, RectSprite
from engine.game.components.falling import Falling
from engine.game.systems import FallingSystem, MovementSystem


def test_falling_applies_gravity_with_terminal_velocity() -> None:
    resources = ResourceStore()
    resources.set("falling_config", {"defaults": {"gravity": 10.0, "terminal_velocity": 5.0}})

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=0.0))
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    world.add_component(eid, Falling())

    falling_sys = FallingSystem(resources)

    falling_sys.update(world, dt=1.0)

    (_, vel) = next(world.view(Velocity))
    assert vel.vy == 5.0  # accelerated by gravity then clamped to terminal


def test_falling_wobble_sets_horizontal_velocity() -> None:
    resources = ResourceStore()
    resources.set("falling_config", {"defaults": {
        "gravity": 0.0,
        "terminal_velocity": 0.0,
        "wobble_amplitude": 10.0,
        "wobble_frequency": 1.0,
        "wobble_phase": 0.0,
    }})

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=0.0))
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    world.add_component(eid, Falling(wobble_amplitude=5.0, wobble_frequency=1.0, wobble_phase=0.0))

    falling_sys = FallingSystem(resources)

    falling_sys.update(world, dt=0.25)  # quarter period -> sin(pi/2)=1

    (_, vel) = next(world.view(Velocity))
    assert vel.vx == 5.0


def test_falling_stops_on_floor_and_marks_grounded() -> None:
    resources = ResourceStore()
    resources.set("falling_config", {"defaults": {"gravity": 10.0, "terminal_velocity": 20.0, "stop_on_floor": True}})

    world = World()
    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=590.0))
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=10.0, height=10.0, color=(0, 0, 0)))
    world.add_component(eid, Falling(stop_on_floor=True))

    falling_sys = FallingSystem(resources)
    move_sys = MovementSystem(resources)

    falling_sys.update(world, dt=1.0)
    move_sys.update(world, dt=1.0)

    _, pos, vel, falling = next(world.view(Position, Velocity, Falling))
    assert pos.y == 590.0
    assert vel.vy == 0.0
    assert vel.vx == 0.0
    assert falling.grounded is True
