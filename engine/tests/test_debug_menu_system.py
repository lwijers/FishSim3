from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.events.input_events import KeyEvent
from engine.game.systems import DebugMenuSystem


def test_f1_toggle_debug_enabled() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)

    world = World()
    sys = DebugMenuSystem(resources)

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

    world = World()
    sys = DebugMenuSystem(resources)

    assert resources.try_get("debug_show_fish_state") is False

    bus.publish(KeyEvent(key="f2", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_show_fish_state") is True

    bus.publish(KeyEvent(key="f2", pressed=True))
    sys.update(world, dt=0.0)
    assert resources.try_get("debug_show_fish_state") is False
