from __future__ import annotations
from typing import List

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.events.input_events import ClickWorld, PointerMove
from engine.game.components import Position, UIHitbox, UIButton, RectSprite, UIElement


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

    def _on_click(self, evt: ClickWorld) -> None:
        self._pending.append(evt)

    def _on_move(self, evt: PointerMove) -> None:
        self._moves.append(evt)

    def update(self, world: World, dt: float) -> None:
        events = self._pending
        moves = self._moves
        self._pending = []
        self._moves = []
        styles = self.resources.try_get("ui_styles", {})
        ui_elem_store = world.get_components(UIElement)

        def style_for_eid(eid):
            ui_elem = ui_elem_store.get(eid)
            style_key = ui_elem.style if ui_elem else None
            return styles.get(style_key, {})

        def color_for_state(eid, state: str):
            style = style_for_eid(eid)
            palette = {
                "inactive": style.get("inactive", (50, 90, 120)),
                "hover": style.get("hover", style.get("active", (90, 170, 210))),
                "active": style.get("active", (90, 170, 210)),
            }
            return tuple(palette.get(state, palette["inactive"]))

        def deactivate_all():
            for eid, _, _, other_btn in world.view(Position, UIHitbox, UIButton):
                other_btn.active = False
                other_btn.hover = False
                rect = world.get_components(RectSprite).get(eid)
                if rect is not None:
                    rect.color = color_for_state(eid, "inactive")
            self.resources.set("active_tool", None)

        def apply_style(eid, button: UIButton):
            rect = world.get_components(RectSprite).get(eid)
            if rect is None:
                return
            if button.active:
                rect.color = color_for_state(eid, "active")
            elif button.hover:
                rect.color = color_for_state(eid, "hover")
            else:
                rect.color = color_for_state(eid, "inactive")

        # Hover handling
        for move in moves:
            for eid, pos, hitbox, button in world.view(Position, UIHitbox, UIButton):
                if not (pos.x <= move.x <= pos.x + hitbox.width and pos.y <= move.y <= pos.y + hitbox.height):
                    button.hover = False
                    apply_style(eid, button)
                    continue

                inside = pos.x <= move.x <= pos.x + hitbox.width and pos.y <= move.y <= pos.y + hitbox.height
                button.hover = inside and not button.active
                apply_style(eid, button)

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
                    # Exclusive group handling
                    if button.exclusive_group:
                        for other_eid, _, _, other_btn in world.view(Position, UIHitbox, UIButton):
                            if other_eid != eid and other_btn.exclusive_group == button.exclusive_group:
                                other_btn.active = False
                                other_btn.hover = False
                                apply_style(other_eid, other_btn)
                    if button.tool_id:
                        self.resources.set("active_tool", button.tool_id)
                else:
                    if self.resources.try_get("active_tool") == button.tool_id:
                        self.resources.set("active_tool", None)
                    button.hover = False

                apply_style(eid, button)
                break
