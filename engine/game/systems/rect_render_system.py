# engine/game/systems/rect_render_system.py
from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components.position import Position
from engine.game.components.rect_sprite import RectSprite


class RectRenderSystem(System):
    """
    Render all RectSprite entities as colored rectangles.
    Works in two spaces:
      - Logical space: Position / RectSprite.width/height.
      - Render space: actual screen pixels (from screen_size).
    We compute a scale factor between logical_size and screen_size
    and draw scaled rectangles, so resizing the window scales the
    whole game world.
    """
    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]
        renderer = resources.try_get("renderer")
        if renderer is None:
            return

        # Sizes
        screen_w, screen_h = resources.try_get("screen_size", FALLBACK_SCREEN_SIZE)
        logical_w, logical_h = resources.try_get("logical_size", (screen_w, screen_h))

        # Avoid division by zero
        if logical_w <= 0:
            logical_w = screen_w
        if logical_h <= 0:
            logical_h = screen_h

        # Non-uniform scaling (simplest: fills the window in both axes)
        scale_x = screen_w / logical_w
        scale_y = screen_h / logical_h

        # Clear screen first
        renderer.clear()

        # Draw all entities that have Position + RectSprite
        for eid, pos, sprite in world.view(Position, RectSprite):
            x_px = pos.x * scale_x
            y_px = pos.y * scale_y
            w_px = sprite.width * scale_x
            h_px = sprite.height * scale_y
            renderer.draw_rect(x_px, y_px, w_px, h_px, sprite.color)

        # Present frame
        renderer.present()
