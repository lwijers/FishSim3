from __future__ import annotations

from dataclasses import dataclass

from engine.ecs import World, System
from engine.scheduling import Scheduler
from engine.resources import ResourceStore
from engine.events import EventBus


# ----------------------------------------------------------------------
# Fake components for this test
# ----------------------------------------------------------------------
@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    x: float
    y: float


# ----------------------------------------------------------------------
# Example systems
# ----------------------------------------------------------------------
class MovementSystem(System):
    phase = "logic"

    def update(self, world: World, dt: float) -> None:
        for eid, pos, vel in world.view(Position, Velocity):
            pos.x += vel.x * dt
            pos.y += vel.y * dt


class EventCountingSystem(System):
    phase = "pre_update"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self.count = 0
        bus: EventBus = resources.get("events")
        bus.subscribe(MyEvent, self.on_event)

    def on_event(self, event: "MyEvent") -> None:
        self.count += 1

    def update(self, world: World, dt: float) -> None:
        # This system just counts events via the callback.
        pass


# Simple event for the EventBus test
@dataclass
class MyEvent:
    value: int


def test_engine_smoke() -> None:
    # Resources
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)

    # World
    world = World()
    eid = world.create_entity()
    world.add_component(eid, Position(0.0, 0.0))
    world.add_component(eid, Velocity(10.0, 0.0))

    # Systems + scheduler
    scheduler = Scheduler()
    move_sys = MovementSystem(resources)
    evt_sys = EventCountingSystem(resources)
    scheduler.add_system(evt_sys)
    scheduler.add_system(move_sys)

    # Publish some events
    bus.publish(MyEvent(1))
    bus.publish(MyEvent(2))

    # Run one frame (dt = 1.0)
    scheduler.update(world, dt=1.0)

    # Assert movement happened
    (only_eid, pos) = next(world.view(Position))
    assert only_eid == eid
    assert pos.x == 10.0
    assert pos.y == 0.0

    # Assert that events were counted via EventBus
    assert evt_sys.count == 2
