# engine/game/systems/sprite_render_system.py
from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components.position import Position
from engine.game.components.velocity import Velocity
from engine.game.components.sprite_ref import SpriteRef


class SpriteRenderSystem(System):
    """
    Render all entities that have Position + SpriteRef as sprites.

    Logical space:
      - Position.x/y and SpriteRef.width/height are in logical units.

    Render space:
      - Uses the same uniform scaling + letterboxing as RectRenderSystem.
      - Does NOT clear or present; we assume some other system (RectRenderSystem)
        owns the frame lifecycle. This lets sprites draw on top of rectangles.
    """

    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]

        renderer = resources.try_get("renderer", None)
        assets = resources.try_get("assets", None)
        if renderer is None or assets is None:
            # No renderer or assets yet (e.g. tests, headless) -> nothing to do.
            return

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
        scale_x = screen_w / logical_w
        scale_y = screen_h / logical_h
        scale = min(scale_x, scale_y)

        # Size of the rendered logical area in screen pixels
        render_w = logical_w * scale
        render_h = logical_h * scale

        # Center it (letterbox/pillarbox)
        offset_x = (screen_w - render_w) / 2.0
        offset_y = (screen_h - render_h) / 2.0

        # Draw all entities that have Position + SpriteRef
        vel_store = world.get_components(Velocity)
        for eid, pos, sprite in world.view(Position, SpriteRef):
            if not assets.has_image(sprite.sprite_id):
                continue

            image = assets.get_image(sprite.sprite_id)

            x_px = offset_x + pos.x * scale
            y_px = offset_y + pos.y * scale
            w_px = sprite.width * scale
            h_px = sprite.height * scale

            flip_x = bool(getattr(sprite, "facing_left", False))
            # Fallback: if no facing flag yet, infer from velocity when present.
            if not flip_x:
                vel = vel_store.get(eid)
                if vel is not None and abs(vel.vx) > 1e-3:
                    flip_x = vel.vx < 0.0

            renderer.draw_image(image, x_px, y_px, w_px, h_px, flip_x=flip_x)

        # Present the composed frame after all sprites have been drawn.
        renderer.present()
