from __future__ import annotations
from typing import Dict

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.events.input_events import KeyEvent
from engine.game.components import UILabel, MouseState
from engine.game.debug import DebugRegistry


class DebugManagerSystem(System):
    """
    Handles debug panel toggles (F-keys), exclusivity, and label text updates via debug text providers.
    """
    phase = "logic"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self._keys: list[KeyEvent] = []
        bus = resources.get("events")
        bus.subscribe(KeyEvent, self._on_key)

        registry = resources.try_get("debug_registry")
        if registry is None:
            cfg = resources.try_get("debug_panels_config", {})
            registry = DebugRegistry.from_config(cfg)
            resources.set("debug_registry", registry)
        self.registry: DebugRegistry = registry

        # Ensure maps exist
        panel_vis = resources.try_get("panel_visibility") or {}
        for pid in self.registry.panels_by_id:
            panel_vis.setdefault(pid, False)
        resources.set("panel_visibility", panel_vis)
        resources.set("active_debug_panel", None)

        # Managed flags default to False
        for panel in self.registry.panels_by_id.values():
            for flag in panel.flags_on:
                resources.set(flag, False)
        resources.set("debug_show_fish_state", bool(resources.try_get("debug_show_fish_state", False)))

        # Built-in provider (FPS/entities/tool/mouse)
        self.registry.register_provider(self._builtin_text_provider)
        self._fps = 0.0
        self._fps_alpha = 0.1

    def _on_key(self, evt: KeyEvent) -> None:
        self._keys.append(evt)

    def update(self, world: World, dt: float) -> None:
        for evt in self._keys:
            key = evt.key.lower()
            if evt.pressed:
                panel = self.registry.panels_by_hotkey.get(key)
                if panel:
                    current = self.resources.try_get("active_debug_panel")
                    next_panel = None if current == panel.panel_id else panel.panel_id
                    self._set_active_panel(next_panel)
                elif key == "f2":
                    cur = bool(self.resources.try_get("debug_show_fish_state", False))
                    self.resources.set("debug_show_fish_state", not cur)
        self._keys = []

        if dt > 0:
            inst_fps = 1.0 / dt
            self._fps = (1 - self._fps_alpha) * self._fps + self._fps_alpha * inst_fps

        text_map: Dict[str, str] = {}
        for provider in self.registry.text_providers:
            text_map.update(provider(world, self.resources))

        for _, label in world.view(UILabel):
            key = label.text_key or label.text
            if key in text_map:
                label.text = text_map[key]

    def _set_active_panel(self, panel_id: str | None) -> None:
        self.resources.set("active_debug_panel", panel_id)
        panel_vis = self.resources.try_get("panel_visibility") or {}
        for pid in self.registry.panels_by_id:
            panel_vis[pid] = False
        if panel_id is not None and panel_id in self.registry.panels_by_id:
            panel_vis[panel_id] = True
        self.resources.set("panel_visibility", panel_vis)

        # Reset all managed flags, then set for the active panel
        managed_flags = set()
        for panel in self.registry.panels_by_id.values():
            managed_flags.update(panel.flags_on)
        for flag in managed_flags:
            self.resources.set(flag, False)
        if panel_id is not None and panel_id in self.registry.panels_by_id:
            for flag in self.registry.panels_by_id[panel_id].flags_on:
                self.resources.set(flag, True)

    def _builtin_text_provider(self, world: World, resources: ResourceStore) -> Dict[str, str]:
        mouse_state = None
        if hasattr(resources, "_mouse_eid"):
            ms_store = world.get_components(MouseState)
            mouse_state = ms_store.get(resources._mouse_eid)
        active_tool = resources.try_get("active_tool")
        entity_count = sum(len(store) for store in world._components.values()) if hasattr(world, "_components") else 0
        return {
            "debug_fps": f"FPS: {self._fps:.1f}",
            "debug_entities": f"Entities: {entity_count}",
            "debug_tool": f"Tool: {active_tool or 'none'}",
            "debug_mouse": f"Mouse: ({mouse_state.x:.0f}, {mouse_state.y:.0f})" if mouse_state else "Mouse: n/a",
        }
