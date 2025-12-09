from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.components import Tank, TankBounds, InTank, Position, RectSprite
from engine.game.components.pellet import Pellet
from engine.game.events.input_events import ClickWorld
from engine.game.systems.placement_system import PlacementSystem


def test_placement_spawns_pellet_inside_tank_and_flushes() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)

    world = World()
    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="t1", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=0.0, y=0.0, width=100.0, height=50.0))

    placement = PlacementSystem(resources)

    bus.publish(ClickWorld(x=10.0, y=20.0))

    placement.update(world, dt=0.0)
    world.flush_commands()

    pellets = list(world.view(Pellet, Position, InTank, RectSprite))
    assert len(pellets) == 1
    eid, pellet, pos, in_tank, rect = pellets[0]
    assert in_tank.tank == tank_eid
    assert pos.x == 10.0
    assert pos.y == 20.0
    assert rect.width == pellet.size
    assert rect.height == pellet.size
