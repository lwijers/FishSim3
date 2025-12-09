from __future__ import annotations
import random

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.components import Position, UIHitbox, UIButton, RectSprite
from engine.game.events.input_events import ClickWorld, PointerMove
from engine.game.systems import UIButtonSystem


def _make_button_world(resources: ResourceStore):
    world = World()
    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=0.0))
    world.add_component(eid, UIHitbox(width=50.0, height=50.0))
    world.add_component(eid, UIButton(tool_id="pellet", active=False))
    world.add_component(eid, RectSprite(width=50.0, height=50.0, color=(1, 1, 1)))
    return world


def test_ui_button_toggle_and_active_tool() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("ui_config", {"buttons": {"palette": {"inactive": [0, 0, 0], "active": [10, 10, 10]}}})

    world = _make_button_world(resources)
    sys = UIButtonSystem(resources)

    bus.publish(ClickWorld(x=10.0, y=10.0, button=1))
    sys.update(world, dt=0.0)

    btn = list(world.view(UIButton))[0][1]
    rect = list(world.view(RectSprite))[0][1]
    assert btn.active is True
    assert resources.try_get("active_tool") == "pellet"
    assert rect.color == (10, 10, 10)

    bus.publish(ClickWorld(x=10.0, y=10.0, button=3))
    sys.update(world, dt=0.0)

    btn = list(world.view(UIButton))[0][1]
    rect = list(world.view(RectSprite))[0][1]
    assert btn.active is False
    assert resources.try_get("active_tool") is None
    assert rect.color == (0, 0, 0)


def test_right_click_anywhere_deactivates() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("ui_config", {"buttons": {"palette": {"inactive": [0, 0, 0], "active": [10, 10, 10]}}})

    world = _make_button_world(resources)
    sys = UIButtonSystem(resources)

    bus.publish(ClickWorld(x=10.0, y=10.0, button=1))
    sys.update(world, dt=0.0)
    assert resources.try_get("active_tool") == "pellet"

    # Right click away from button still deactivates
    bus.publish(ClickWorld(x=999.0, y=999.0, button=3))
    sys.update(world, dt=0.0)
    btn = list(world.view(UIButton))[0][1]
    rect = list(world.view(RectSprite))[0][1]
    assert btn.active is False
    assert resources.try_get("active_tool") is None
    assert rect.color == (0, 0, 0)


def test_hover_color_applies_when_inactive() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("ui_config", {"buttons": {"palette": {"inactive": [0, 0, 0], "active": [10, 10, 10], "hover": [5, 5, 5]}}})

    world = _make_button_world(resources)
    sys = UIButtonSystem(resources)

    bus.publish(PointerMove(x=10.0, y=10.0))
    sys.update(world, dt=0.0)

    btn = list(world.view(UIButton))[0][1]
    rect = list(world.view(RectSprite))[0][1]
    assert btn.hover is True
    assert btn.active is False
    assert rect.color == (5, 5, 5)
