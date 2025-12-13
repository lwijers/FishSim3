from __future__ import annotations
import math

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components import Position, Velocity, MovementIntent, RectSprite


class MovementDebugSystem(System):
    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources
        if not resources.try_get("debug_show_vectors", False):
            return

        renderer = resources.try_get("renderer")
        if renderer is None or not hasattr(renderer, "draw_line"):
            return

        cfg = resources.try_get("movement_config", {})
        dbg = cfg.get("debug", {})
        scale = float(dbg.get("vector_scale", 0.2))
        arrow_size = float(dbg.get("arrow_size", 6.0))
        col_v = tuple(dbg.get("color_velocity", (0, 200, 255)))
        col_i = tuple(dbg.get("color_intent", (255, 200, 0)))
        col_t = tuple(dbg.get("color_target", (0, 255, 120)))

        screen_w, screen_h = resources.try_get("screen_size", (1280, 720))
        logical_w, logical_h = resources.try_get("logical_size", (1280, 720))

        uniform = min(screen_w / logical_w, screen_h / logical_h)
        off_x = (screen_w - logical_w * uniform) / 2.0
        off_y = (screen_h - logical_h * uniform) / 2.0

        intents = world.get_components(MovementIntent)

        for eid, pos, vel in world.view(Position, Velocity):
            # Convert world pos → screen pos
            x = off_x + pos.x * uniform
            y = off_y + pos.y * uniform

            # Correct velocity → screen scaling
            vx = vel.vx * scale * uniform
            vy = vel.vy * scale * uniform

            # Draw velocity vector
            renderer.draw_line((x, y), (x + vx, y + vy), color=col_v, width=2)
            self._arrow(renderer, x + vx, y + vy, vel.vx, vel.vy, col_v, arrow_size)

            intent = intents.get(eid)
            if intent:
                if intent.debug_target is not None:
                    tx, ty = intent.debug_target
                    sx = off_x + tx * uniform
                    sy = off_y + ty * uniform
                    renderer.draw_line((x, y), (sx, sy), color=col_t, width=1)
                    renderer.draw_line((x, y), (sx, sy), color=col_i, width=2)
                    self._arrow(renderer, sx, sy, tx - pos.x, ty - pos.y, col_i, arrow_size)
                else:
                    ivx = intent.target_vx * scale * uniform
                    ivy = intent.target_vy * scale * uniform
                    renderer.draw_line((x, y), (x + ivx, y + ivy),
                                       color=col_i, width=2)
                    self._arrow(renderer, x + ivx, y + ivy,
                                intent.target_vx, intent.target_vy,
                                col_i, arrow_size)


    def _arrow(self, renderer, tip_x, tip_y, dx, dy, color, size):
        """Stable arrowhead even when dx/dy are tiny (uses normalized direction)."""
        mag = math.hypot(dx, dy)
        if mag < 1e-3:
            return  # direction unknown

        ux = dx / mag
        uy = dy / mag

        # Arrowhead: two wings rotated ±150°
        angle = math.radians(150)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Rotate
        lx = ux * cos_a - uy * sin_a
        ly = ux * sin_a + uy * cos_a
        rx = ux * cos_a + uy * sin_a
        ry = -ux * sin_a + uy * cos_a

        renderer.draw_line(
            (tip_x, tip_y),
            (tip_x + lx * size, tip_y + ly * size),
            color=color
        )
        renderer.draw_line(
            (tip_x, tip_y),
            (tip_x + rx * size, tip_y + ry * size),
            color=color
        )
