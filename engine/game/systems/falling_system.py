from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.components import Velocity
from engine.game.components.falling import Falling


class FallingSystem(System):
    """
    Applies gravity and terminal velocity to entities with Falling + Velocity.
    Grounded entities that stop on the floor are skipped.
    """
    phase = "logic"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]
        cfg = resources.try_get("falling_config", {}).get("defaults", {})
        default_g = float(cfg.get("gravity", 0.0))
        default_term = float(cfg.get("terminal_velocity", 0.0))
        default_stop = bool(cfg.get("stop_on_floor", True))

        for eid, vel, falling in world.view(Velocity, Falling):
            # Skip if already grounded and meant to stop.
            if falling.stop_on_floor and falling.grounded:
                continue

            g = falling.gravity if falling.gravity is not None else default_g
            term = falling.terminal_velocity if falling.terminal_velocity is not None else default_term
            stop = falling.stop_on_floor if falling.stop_on_floor is not None else default_stop
            falling.stop_on_floor = stop  # normalize potential None

            # Apply gravity
            vel.vy += g * dt

            # Clamp downward speed
            if term > 0.0:
                if g >= 0.0:
                    vel.vy = min(vel.vy, term)
                else:
                    vel.vy = max(vel.vy, -term)
