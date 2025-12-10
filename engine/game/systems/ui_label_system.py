from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.components import Position, UILabel, UIElement
from engine.game.components.ui_hitbox import UIHitbox


class UILabelSystem(System):
    """
    Renders UILabels via the renderer's draw_text (adapter-provided).
    """
    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]

        renderer = resources.try_get("renderer")
        if renderer is None or not hasattr(renderer, "draw_text"):
            return

        styles = resources.try_get("ui_styles", {})
        panel_visibility = resources.try_get("panel_visibility", {})
        panel_links = resources.try_get("ui_panel_links", {})
        for eid, pos, label, ui_elem in world.view(Position, UILabel, UIElement):
            if ui_elem.visible_flag and not resources.try_get(ui_elem.visible_flag, False):
                continue
            # If attached to a panel, respect panel visibility flag
            panel_id = panel_links.get(eid)
            if panel_id is not None and panel_id in panel_visibility and not panel_visibility.get(panel_id, False):
                continue
            style = styles.get(ui_elem.style, {})
            color = tuple(style.get("text_color", (255, 255, 255)))
            font_size = int(style.get("font_size", 16))
            font_name = style.get("font_name")
            renderer.draw_text(label.text, pos.x, pos.y, color=color, font_size=font_size, font_name=font_name)
