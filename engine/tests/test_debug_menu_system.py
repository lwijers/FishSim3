from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.events.input_events import KeyEvent
from engine.game.components import UILabel
from engine.game.systems import DebugManagerSystem


def test_f1_toggle_debug_enabled() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set(
        "debug_panels_config",
        {
            "panels": [
                {"id": "debug_panel", "toggle_key": "f1", "flags_on": ["debug_enabled"]},
                {"id": "motion_debug_panel", "toggle_key": "f3", "flags_on": ["debug_show_vectors"]},
            ]
        },
    )

    world = World()
    sys = DebugManagerSystem(resources)

    assert resources.try_get("debug_enabled") is False

    bus.publish(KeyEvent(key="f1", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_enabled") is True

    bus.publish(KeyEvent(key="f1", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_enabled") is False


def test_f2_toggle_fish_state() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set(
        "debug_panels_config",
        {
            "panels": [
                {"id": "debug_panel", "toggle_key": "f1", "flags_on": ["debug_enabled"]},
                {"id": "motion_debug_panel", "toggle_key": "f3", "flags_on": ["debug_show_vectors"]},
            ]
        },
    )

    world = World()
    sys = DebugManagerSystem(resources)

    assert resources.try_get("debug_show_fish_state") is False

    bus.publish(KeyEvent(key="f2", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_show_fish_state") is True

    bus.publish(KeyEvent(key="f2", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_show_fish_state") is False


def test_debug_panels_are_exclusive_and_toggle_flags() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set(
        "debug_panels_config",
        {
            "panels": [
                {"id": "debug_panel", "toggle_key": "f1", "flags_on": ["debug_enabled"]},
                {"id": "motion_debug_panel", "toggle_key": "f3", "flags_on": ["debug_show_vectors"]},
            ]
        },
    )
    resources.set("panel_visibility", {})

    world = World()
    sys = DebugManagerSystem(resources)

    # Toggle debug panel on
    bus.publish(KeyEvent(key="f1", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("active_debug_panel") == "debug_panel"
    assert resources.try_get("debug_enabled") is True
    panel_vis = resources.try_get("panel_visibility", {})
    assert panel_vis.get("debug_panel") is True
    assert panel_vis.get("motion_debug_panel") is False

    # Switch to motion debug panel; should hide the other
    bus.publish(KeyEvent(key="f3", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("active_debug_panel") == "motion_debug_panel"
    panel_vis = resources.try_get("panel_visibility", {})
    assert panel_vis.get("debug_panel") is False
    assert panel_vis.get("motion_debug_panel") is True
    assert resources.try_get("debug_show_vectors") is True
    assert resources.try_get("debug_enabled") is False

    # Toggle off motion panel
    bus.publish(KeyEvent(key="f3", pressed=True))
    sys.update(world, dt=0.0)
    panel_vis = resources.try_get("panel_visibility", {})
    assert resources.try_get("active_debug_panel") is None
    assert panel_vis.get("debug_panel") is False
    assert panel_vis.get("motion_debug_panel") is False
    assert resources.try_get("debug_show_vectors") is False


def test_debug_text_provider_updates_labels() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set(
        "debug_panels_config",
        {"panels": [{"id": "debug_panel", "toggle_key": "f1", "flags_on": ["debug_enabled"]}]},
    )
    resources.set("panel_visibility", {})

    world = World()
    eid = world.create_entity()
    world.add_component(eid, UILabel(text="foo", text_key="foo"))

    sys = DebugManagerSystem(resources)
    registry = resources.get("debug_registry")
    registry.register_provider(lambda w, r: {"foo": "bar"})

    bus.publish(KeyEvent(key="f1", pressed=True))
    sys.update(world, dt=0.0)

    assert world.get_components(UILabel)[eid].text == "bar"
