from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components import Position, Fish, Brain, RectSprite, SpriteRef


class FishStateLabelSystem(System):
    """
    Renders fish brain state below each fish when debug_show_fish_state is true.
    """
    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]
        if not resources.try_get("debug_show_fish_state", False):
            return

        renderer = resources.try_get("renderer")
        if renderer is None or not hasattr(renderer, "draw_text"):
            return

        styles = resources.try_get("ui_styles", {})
        style = styles.get("fish_state_text", {})
        color = tuple(style.get("text_color", (255, 255, 255)))
        font_size = int(style.get("font_size", 12))
        font_name = style.get("font_name")
        offset_y = float(style.get("offset_y", 8.0))

        # Screen/logical sizes
        screen_w, screen_h = resources.try_get("screen_size", FALLBACK_SCREEN_SIZE)
        logical_w, logical_h = resources.try_get("logical_size", (screen_w, screen_h))
        if logical_w <= 0:
            logical_w = screen_w
        if logical_h <= 0:
            logical_h = screen_h

        scale_x = screen_w / logical_w
        scale_y = screen_h / logical_h
        scale = min(scale_x, scale_y)
        render_w = logical_w * scale
        render_h = logical_h * scale
        offset_x = (screen_w - render_w) / 2.0
        offset_y_screen = (screen_h - render_h) / 2.0

        rect_store = world.get_components(RectSprite)
        sprite_store = world.get_components(SpriteRef)

        for eid, pos, fish, brain in world.view(Position, Fish, Brain):
            height = 0.0
            rect = rect_store.get(eid)
            if rect is not None:
                height = rect.height
            else:
                sprite_ref = sprite_store.get(eid)
                if sprite_ref is not None:
                    height = sprite_ref.height

            x_px = offset_x + pos.x * scale
            y_px = offset_y_screen + (pos.y + height + offset_y) * scale
            renderer.draw_text(brain.state, x_px, y_px, color=color, font_size=font_size, font_name=font_name)
