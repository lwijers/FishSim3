from __future__ import annotations
from typing import List, Tuple
from engine.ecs import System, World
from engine.ecs.commands import CreateEntityCmd
from engine.resources import ResourceStore
from engine.game.components import Position, RectSprite, InTank, TankBounds, Tank, UIHitbox, UIElement, MouseState
from engine.game.components.pellet import Pellet
from engine.game.events.input_events import ClickWorld
from engine.game.factories.pellet_factory import create_pellet_cmd
import random

class PlacementSystem(System):
    """Listens for ClickWorld events and queues pellet creation inside tanks."""
    phase = "logic"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self._pending: List[ClickWorld] = []
        bus = resources.get("events")
        bus.subscribe(ClickWorld, self._on_click)
        self._pellet_cfg = resources.try_get("pellet_config", {}).get("pellet", {})
        self._rng = resources.try_get("rng_spawns")
        if self._rng is None:
            self._rng = random.Random(42)

    def _on_click(self, event: ClickWorld) -> None:
        self._pending.append(event)

    def _find_tank_at(self, world: World, x: float, y: float) -> Tuple[int | None, TankBounds | None]:
        for eid, tank, bounds in world.view(Tank, TankBounds):
            if bounds.x <= x <= bounds.x + bounds.width and bounds.y <= y <= bounds.y + bounds.height:
                return eid, bounds
        return None, None

    def update(self, world: World, dt: float) -> None:
        if not self._pending:
            return

        events = self._pending
        self._pending = []

        for evt in events:
            if self._ui_hit(world, evt.x, evt.y):
                continue
            # Only spawn if pellet tool is active
            if self.resources.try_get("active_tool") != "pellet":
                continue

            tank_eid, bounds = self._find_tank_at(world, evt.x, evt.y)
            if tank_eid is None or bounds is None:
                continue

            size = float(self._pellet_cfg.get("size", 0.0))
            clamped_x = max(bounds.x, min(evt.x, bounds.x + bounds.width - size))
            clamped_y = max(bounds.y, min(evt.y, bounds.y + bounds.height - size))

            cmd: CreateEntityCmd = create_pellet_cmd(
                clamped_x,
                clamped_y,
                tank_eid,
                pellet_cfg=self._pellet_cfg,
                rng=self._rng,
            )
            world.queue_command(cmd)

    def _ui_hit(self, world: World, x: float, y: float) -> bool:
        panel_links = self.resources.try_get("ui_panel_links", {})
        panel_visibility = self.resources.try_get("panel_visibility", {})

        for eid, pos_ui, hitbox_ui in world.view(Position, UIHitbox):
            ui_elem = world.get_components(UIElement).get(eid)
            if ui_elem and ui_elem.visible_flag and not self.resources.try_get(ui_elem.visible_flag, False):
                continue
            panel_id = panel_links.get(eid)
            if panel_id is not None and panel_id in panel_visibility:
                if not panel_visibility.get(panel_id, False):
                    continue
            if pos_ui.x <= x <= pos_ui.x + hitbox_ui.width and pos_ui.y <= y <= pos_ui.y + hitbox_ui.height:
                return True
        for eid, pos_ui, ui_elem in world.view(Position, UIElement):
            if ui_elem.visible_flag and not self.resources.try_get(ui_elem.visible_flag, False):
                continue
            panel_id = panel_links.get(eid)
            if panel_id is not None and panel_id in panel_visibility:
                if not panel_visibility.get(panel_id, False):
                    continue
            if pos_ui.x <= x <= pos_ui.x + ui_elem.width and pos_ui.y <= y <= pos_ui.y + ui_elem.height:
                return True
        return False
