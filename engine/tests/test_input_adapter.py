from __future__ import annotations

from engine.resources import ResourceStore
from engine.events import EventBus
from engine.adapters.pygame_input.input_adapter import InputAdapter
from engine.game.events.input_events import ClickWorld

class DummyBus(EventBus):
    def __init__(self):
        super().__init__()
        self.events = []

    def publish(self, event):
        self.events.append(event)
        super().publish(event)


def test_input_adapter_maps_screen_to_logical_and_filters_letterbox():
    resources = ResourceStore()
    bus = DummyBus()
    resources.register("events", bus)
    resources.set("screen_size", (800, 600))
    resources.set("logical_size", (400, 300))

    adapter = InputAdapter(resources)

    logical = adapter._to_logical((200, 150))
    assert logical == (100.0, 75.0)

    # Outside letterboxed area (too far left)
    assert adapter._to_logical((-10, 150)) is None
