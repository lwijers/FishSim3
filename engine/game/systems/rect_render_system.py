# engine/game/systems/rect_render_system.py
from __future__ import annotations
from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components.position import Position
from engine.game.components.rect_sprite import RectSprite
from engine.game.components.sprite_ref import SpriteRef
from engine.game.components.ui_element import UIElement


class RectRenderSystem(System):
    """
    Render all RectSprite entities as colored rectangles.

    Logical space:
      - Position.x/y and RectSprite.width/height are in *logical* units
        (e.g. 0..1280, 0..720).

    Render space:
      - We scale logical space uniformly to fit inside the window while
        preserving aspect ratio (no stretching).
      - The game view is letterboxed (centered) if the window aspect
        ratio doesn't match the logical aspect ratio.
    """
    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]

        renderer = resources.try_get("renderer")
        if renderer is None:
            return

        sprite_ref_store = world.get_components(SpriteRef)

        # Current window size (updated by PygameApp on resize)
        screen_w, screen_h = resources.try_get("screen_size", FALLBACK_SCREEN_SIZE)

        # Fixed logical size (from settings.json), or fall back to screen size
        logical_w, logical_h = resources.try_get("logical_size", (screen_w, screen_h))

        # Avoid division by zero
        if logical_w <= 0:
            logical_w = screen_w
        if logical_h <= 0:
            logical_h = screen_h

        # --- UNIFORM SCALE (keep proportions) ---
        # scale = min(scale_x, scale_y)
        scale_x = screen_w / logical_w
        scale_y = screen_h / logical_h
        scale = min(scale_x, scale_y)

        # Size of the rendered logical area in screen pixels
        render_w = logical_w * scale
        render_h = logical_h * scale

        # Center it (letterbox/pillarbox)
        offset_x = (screen_w - render_w) / 2.0
        offset_y = (screen_h - render_h) / 2.0

        # Clear whole screen first
        renderer.clear()

        # Borders metadata from UI (optional)
        borders = resources.try_get("ui_borders", {})
        styles = resources.try_get("ui_styles", {})
        ui_elem_store = world.get_components(UIElement)

        # Draw all entities that have Position + RectSprite
        drew_any = False
        for eid, pos, sprite in world.view(Position, RectSprite):
            # If this entity also has a SpriteRef, skip drawing the fallback rect.
            if eid in sprite_ref_store:
                continue
            x_px = offset_x + pos.x * scale
            y_px = offset_y + pos.y * scale
            w_px = sprite.width * scale
            h_px = sprite.height * scale
            border = borders.get(eid)
            if border is None:
                ui_elem = ui_elem_store.get(eid)
                style_key = ui_elem.style if ui_elem else None
                style = styles.get(style_key, {}) if style_key else {}
                if "border" in style or "border_width" in style or "corner_radius" in style:
                    border = (
                        tuple(style.get("border", (20, 40, 60))),
                        int(style.get("border_width", 0)),
                        int(style.get("corner_radius", 0)),
                    )
            if border:
                border_color, border_width, corner_radius = border
                renderer.draw_rect(x_px, y_px, w_px, h_px, border_color, outline_width=border_width, border_radius=corner_radius)
                renderer.draw_rect(
                    x_px + border_width,
                    y_px + border_width,
                    w_px - 2 * border_width,
                    h_px - 2 * border_width,
                    sprite.color,
                    outline_width=0,
                    border_radius=max(0, corner_radius - border_width),
                )
            else:
                renderer.draw_rect(x_px, y_px, w_px, h_px, sprite.color)
            drew_any = True

        # If sprites are present in the world, let SpriteRenderSystem own present().
        # Otherwise, present here for pure-rect scenes/tests.
        if drew_any and not sprite_ref_store:
            renderer.present()
