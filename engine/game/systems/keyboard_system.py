from __future__ import annotations
from engine.ecs import System, World
from engine.game.components.keyboard_state import KeyboardState
from engine.game.events.input_events import KeyEvent


class KeyboardSystem(System):
    """
    Tracks keyboard state in a KeyboardState resource component stored on a singleton entity.
    """
    phase = "logic"

    def __init__(self, resources) -> None:
        super().__init__(resources)
        self._pending: list[KeyEvent] = []
        bus = resources.get("events")
        bus.subscribe(KeyEvent, self._on_key)

    def _on_key(self, evt: KeyEvent) -> None:
        self._pending.append(evt)

    def update(self, world: World, dt: float) -> None:
        if not self._pending:
            return

        if not hasattr(self.resources, "_keyboard_eid"):
            eid = world.create_entity()
            world.add_component(eid, KeyboardState())
            self.resources._keyboard_eid = eid
        eid = self.resources._keyboard_eid
        state_store = world.get_components(KeyboardState)
        kb = state_store.get(eid)
        if kb is None:
            kb = KeyboardState()
            world.add_component(eid, kb)

        for evt in self._pending:
            kb.keys[evt.key] = evt.pressed

        self._pending = []
