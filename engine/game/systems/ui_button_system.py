from __future__ import annotations
from typing import List

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.events.input_events import ClickWorld, PointerMove
from engine.game.components import Position, UIHitbox, UIButton, RectSprite


class UIButtonSystem(System):
    """
    Handles UI button toggling and active tool selection.
    Left click toggles, right click deactivates. Activating one tool deactivates others.
    """
    phase = "logic"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self._pending: List[ClickWorld] = []
        self._moves: List[PointerMove] = []
        bus = resources.get("events")
        bus.subscribe(ClickWorld, self._on_click)
        bus.subscribe(PointerMove, self._on_move)

        ui_cfg = resources.try_get("ui_config", {})
        buttons_cfg = ui_cfg.get("buttons", {})
        palette = buttons_cfg.get("palette", {})
        self._color_inactive = tuple(palette.get("inactive", (50, 90, 120)))
        self._color_active = tuple(palette.get("active", (90, 170, 210)))
        self._color_hover = tuple(palette.get("hover", self._color_active))
        self._border_color = tuple(palette.get("border", (20, 40, 60)))
        self._border_width = int(buttons_cfg.get("border_width", 2))
        self._corner_radius = int(buttons_cfg.get("corner_radius", 8))

    def _on_click(self, evt: ClickWorld) -> None:
        self._pending.append(evt)

    def _on_move(self, evt: PointerMove) -> None:
        self._moves.append(evt)

    def update(self, world: World, dt: float) -> None:
        events = self._pending
        moves = self._moves
        self._pending = []
        self._moves = []

        def deactivate_all():
            for eid, _, _, other_btn in world.view(Position, UIHitbox, UIButton):
                other_btn.active = False
                other_btn.hover = False
                rect = world.get_components(RectSprite).get(eid)
                if rect is not None:
                    rect.color = self._color_inactive
            self.resources.set("active_tool", None)

        # Hover handling
        for move in moves:
            for eid, pos, hitbox, button in world.view(Position, UIHitbox, UIButton):
                inside = pos.x <= move.x <= pos.x + hitbox.width and pos.y <= move.y <= pos.y + hitbox.height
                button.hover = inside and not button.active
                rect = world.get_components(RectSprite).get(eid)
                if rect is not None:
                    if button.active:
                        rect.color = self._color_active
                    elif button.hover:
                        rect.color = self._color_hover
                    else:
                        rect.color = self._color_inactive

        for evt in events:
            # Right-click anywhere should deactivate the current tool/buttons.
            if evt.button == 3:
                deactivate_all()
                continue

            for eid, pos, hitbox, button in world.view(Position, UIHitbox, UIButton):
                if not (pos.x <= evt.x <= pos.x + hitbox.width and pos.y <= evt.y <= pos.y + hitbox.height):
                    continue

                if evt.button == 1:
                    button.active = not button.active
                else:
                    continue

                # If activating this button, deactivate others.
                if button.active:
                    for other_eid, _, _, other_btn in world.view(Position, UIHitbox, UIButton):
                        if other_eid != eid:
                            other_btn.active = False
                            other_btn.hover = False
                    self.resources.set("active_tool", button.tool_id)
                else:
                    if self.resources.try_get("active_tool") == button.tool_id:
                        self.resources.set("active_tool", None)
                    button.hover = False

                # Update visual state
                rect = world.get_components(RectSprite).get(eid)
                if rect is not None:
                    if button.active:
                        rect.color = self._color_active
                    elif button.hover:
                        rect.color = self._color_hover
                    else:
                        rect.color = self._color_inactive
                break
