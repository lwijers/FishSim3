from __future__ import annotations
from engine.ecs import System, World
from engine.game.components.mouse_state import MouseState
from engine.game.events.input_events import ClickWorld, PointerMove


class MouseSystem(System):
    """
    Tracks mouse position/buttons in MouseState stored on a singleton entity.
    """
    phase = "logic"

    def __init__(self, resources) -> None:
        super().__init__(resources)
        self._clicks: list[ClickWorld] = []
        self._moves: list[PointerMove] = []
        bus = resources.get("events")
        bus.subscribe(ClickWorld, self._on_click)
        bus.subscribe(PointerMove, self._on_move)

    def _on_click(self, evt: ClickWorld) -> None:
        self._clicks.append(evt)

    def _on_move(self, evt: PointerMove) -> None:
        self._moves.append(evt)

    def update(self, world: World, dt: float) -> None:
        if not self._clicks and not self._moves:
            return

        if not hasattr(self.resources, "_mouse_eid"):
            eid = world.create_entity()
            world.add_component(eid, MouseState())
            self.resources._mouse_eid = eid
        eid = self.resources._mouse_eid
        state_store = world.get_components(MouseState)
        ms = state_store.get(eid)
        if ms is None:
            ms = MouseState()
            world.add_component(eid, ms)

        for move in self._moves:
            ms.x = move.x
            ms.y = move.y

        for click in self._clicks:
            ms.buttons[click.button] = True  # transient; cleared on release? (future)

        self._clicks = []
        self._moves = []
