from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.components import Tank, TankBounds, InTank, Position, RectSprite, Falling
from engine.game.components.pellet import Pellet
from engine.game.events.input_events import ClickWorld
from engine.game.systems.placement_system import PlacementSystem
import random


def test_placement_spawns_pellet_inside_tank_and_flushes() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("pellet_config", {"pellet": {
        "size": 12.0,
        "color": [1, 2, 3],
        "sprite_id": "pellet",
        "falling": {
            "gravity": 100.0,
            "terminal_velocity": 160.0,
            "wobble_amplitude_range": [5.0, 5.0],
            "wobble_frequency_range": [1.0, 1.0],
            "wobble_phase_range": [0.0, 0.0],
            "stop_on_floor": True,
        },
    }})
    resources.set("rng_spawns", random.Random(123))
    resources.set("active_tool", "pellet")

    world = World()
    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="t1", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=0.0, y=0.0, width=100.0, height=50.0))

    placement = PlacementSystem(resources)

    bus.publish(ClickWorld(x=10.0, y=20.0))

    placement.update(world, dt=0.0)
    world.flush_commands()

    pellets = list(world.view(Pellet, Position, InTank, RectSprite, Falling))
    assert len(pellets) == 1
    eid, pellet, pos, in_tank, rect, falling = pellets[0]
    assert in_tank.tank == tank_eid
    assert pos.x == 10.0
    assert pos.y == 20.0
    assert rect.width == pellet.size == 12.0
    assert rect.height == pellet.size == 12.0
    assert rect.color == (1, 2, 3)
    assert falling.stop_on_floor is True


def test_click_on_ui_does_not_spawn() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("pellet_config", {"pellet": {"size": 12.0, "color": [1, 2, 3], "sprite_id": "pellet"}})
    resources.set("rng_spawns", random.Random(123))
    resources.set("active_tool", "pellet")

    world = World()
    # UI element at origin size 20x20
    ui_eid = world.create_entity()
    world.add_component(ui_eid, Position(x=0.0, y=0.0))
    world.add_component(ui_eid, RectSprite(width=20.0, height=20.0, color=(0, 0, 0)))
    from engine.game.components import UIHitbox, UIButton
    world.add_component(ui_eid, UIHitbox(width=20.0, height=20.0))
    world.add_component(ui_eid, UIButton(tool_id="pellet"))

    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="t1", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=0.0, y=0.0, width=100.0, height=50.0))

    placement = PlacementSystem(resources)

    bus.publish(ClickWorld(x=10.0, y=10.0))

    placement.update(world, dt=0.0)
    world.flush_commands()

    # No pellets spawned because UI hitbox consumed
    assert len(list(world.view(Pellet))) == 0
