from __future__ import annotations

import random

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.components import Position, RectSprite, Tank, TankBounds, Pellet, UIElement, UIHitbox
from engine.game.events.input_events import ClickWorld
from engine.game.systems import PlacementSystem


def test_click_on_hidden_ui_allows_spawn() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("pellet_config", {"pellet": {"size": 10.0, "color": [1, 1, 1], "sprite_id": "pellet"}})
    resources.set("rng_spawns", random.Random(1))
    resources.set("active_tool", "pellet")
    resources.set("panel_visibility", {"panel": False})
    resources.set("ui_panel_links", {})

    world = World()
    ui_eid = world.create_entity()
    world.add_component(ui_eid, Position(x=0.0, y=0.0))
    world.add_component(ui_eid, RectSprite(width=20.0, height=20.0, color=(0, 0, 0)))
    world.add_component(ui_eid, UIHitbox(width=20.0, height=20.0))
    world.add_component(ui_eid, UIElement(width=20.0, height=20.0, style=None, element_id="panel", visible_flag=None))
    resources.get("ui_panel_links")[ui_eid] = "panel"

    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="t", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=0.0, y=0.0, width=100.0, height=100.0))

    placement = PlacementSystem(resources)
    bus.publish(ClickWorld(x=10.0, y=10.0))
    placement.update(world, dt=0.0)
    world.flush_commands()

    # panel hidden -> click ignored for UI, pellet spawns
    assert len(list(world.view(Pellet))) == 1


def test_click_on_visible_ui_blocks_spawn() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("pellet_config", {"pellet": {"size": 10.0, "color": [1, 1, 1], "sprite_id": "pellet"}})
    resources.set("rng_spawns", random.Random(1))
    resources.set("active_tool", "pellet")
    resources.set("panel_visibility", {"panel": True})
    resources.set("ui_panel_links", {})

    world = World()
    ui_eid = world.create_entity()
    world.add_component(ui_eid, Position(x=0.0, y=0.0))
    world.add_component(ui_eid, RectSprite(width=20.0, height=20.0, color=(0, 0, 0)))
    world.add_component(ui_eid, UIHitbox(width=20.0, height=20.0))
    world.add_component(ui_eid, UIElement(width=20.0, height=20.0, style=None, element_id="panel", visible_flag=None))
    resources.get("ui_panel_links")[ui_eid] = "panel"

    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="t", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=0.0, y=0.0, width=100.0, height=100.0))

    placement = PlacementSystem(resources)
    bus.publish(ClickWorld(x=10.0, y=10.0))
    placement.update(world, dt=0.0)
    world.flush_commands()

    # panel visible -> click consumed, no pellet spawned
    assert len(list(world.view(Pellet))) == 0
