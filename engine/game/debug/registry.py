from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from engine.ecs import World
from engine.resources import ResourceStore

DebugTextProvider = Callable[[World, ResourceStore], Dict[str, str]]


@dataclass
class DebugPanel:
    hotkey: str
    panel_id: str
    flags_on: List[str] = field(default_factory=list)
    exclusive_group: Optional[str] = "debug"


class DebugRegistry:
    """
    Data-driven registry for debug panels and text providers.
    """

    def __init__(self, panels: Optional[List[DebugPanel]] = None) -> None:
        self.panels_by_hotkey: Dict[str, DebugPanel] = {}
        self.panels_by_id: Dict[str, DebugPanel] = {}
        self.text_providers: List[DebugTextProvider] = []
        if panels:
            for panel in panels:
                self.add_panel(panel)

    @classmethod
    def from_config(cls, cfg: Dict) -> "DebugRegistry":
        panels: List[DebugPanel] = []
        for item in cfg.get("panels", []):
            hotkey = str(item.get("toggle_key") or item.get("hotkey", "")).lower()
            panel_id = item.get("id") or item.get("panel_id")
            if not hotkey or not panel_id:
                continue
            flags = item.get("flags_on", [])
            if isinstance(flags, str):
                flags = [flags]
            exclusive_group = item.get("exclusive_group", "debug")
            panels.append(DebugPanel(hotkey=hotkey, panel_id=panel_id, flags_on=list(flags), exclusive_group=exclusive_group))

        # Fallback defaults if config is empty/missing
        if not panels:
            panels = [
                DebugPanel(hotkey="f1", panel_id="debug_panel", flags_on=["debug_enabled"], exclusive_group="debug"),
                DebugPanel(hotkey="f3", panel_id="motion_debug_panel", flags_on=["debug_show_vectors"], exclusive_group="debug"),
            ]
        return cls(panels)

    def add_panel(self, panel: DebugPanel) -> None:
        self.panels_by_hotkey[panel.hotkey.lower()] = panel
        self.panels_by_id[panel.panel_id] = panel

    def register_provider(self, provider: DebugTextProvider) -> None:
        if provider not in self.text_providers:
            self.text_providers.append(provider)
