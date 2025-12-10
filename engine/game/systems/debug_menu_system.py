from __future__ import annotations
from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.events.input_events import KeyEvent
from engine.game.components import UILabel, MouseState


class DebugMenuSystem(System):
    """
    Toggles debug UI on F1 and updates label texts.
    """
    phase = "logic"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self._keys: list[KeyEvent] = []
        bus = resources.get("events")
        bus.subscribe(KeyEvent, self._on_key)
        # default off
        resources.set("debug_enabled", False)
        resources.set("debug_show_fish_state", False)
        self._fps = 0.0
        self._fps_alpha = 0.1

    def _on_key(self, evt: KeyEvent) -> None:
        self._keys.append(evt)

    def update(self, world: World, dt: float) -> None:
        for evt in self._keys:
            if evt.key.lower() == "f1" and evt.pressed:
                current = bool(self.resources.try_get("debug_enabled", False))
                self.resources.set("debug_enabled", not current)
                self.resources.set("panel_visibility", {"debug_panel": self.resources.try_get("debug_enabled", False)})
            if evt.key.lower() == "f2" and evt.pressed:
                cur = bool(self.resources.try_get("debug_show_fish_state", False))
                self.resources.set("debug_show_fish_state", not cur)
        self._keys = []

        if not self.resources.try_get("debug_enabled", False):
            return

        # FPS estimate (simple EMA)
        if dt > 0:
            inst_fps = 1.0 / dt
            self._fps = (1 - self._fps_alpha) * self._fps + self._fps_alpha * inst_fps

        # Mouse info
        mouse_state = None
        if hasattr(self.resources, "_mouse_eid"):
            ms_store = world.get_components(MouseState)
            mouse_state = ms_store.get(self.resources._mouse_eid)

        # Update debug labels
        active_tool = self.resources.try_get("active_tool")
        text_map = {
            "debug_fps": f"FPS: {self._fps:.1f}",
            "debug_entities": f"Entities: {sum(len(store) for store in world._components.values())}",
            "debug_tool": f"Tool: {active_tool or 'none'}",
            "debug_mouse": f"Mouse: ({mouse_state.x:.0f}, {mouse_state.y:.0f})" if mouse_state else "Mouse: n/a",
        }

        for eid, label in world.view(UILabel):
            key = label.text_key or label.text
            if key in text_map:
                label.text = text_map[key]
