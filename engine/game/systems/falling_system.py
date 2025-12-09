from __future__ import annotations

import math
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
        default_wobble_amp = float(cfg.get("wobble_amplitude", 0.0))
        default_wobble_freq = float(cfg.get("wobble_frequency", 0.0))
        default_wobble_phase = float(cfg.get("wobble_phase", 0.0))

        for eid, vel, falling in world.view(Velocity, Falling):
            # Skip if already grounded and meant to stop.
            if falling.stop_on_floor and falling.grounded:
                continue

            g = falling.gravity if falling.gravity is not None else default_g
            term = falling.terminal_velocity if falling.terminal_velocity is not None else default_term
            stop = falling.stop_on_floor if falling.stop_on_floor is not None else default_stop
            amp = falling.wobble_amplitude if falling.wobble_amplitude is not None else default_wobble_amp
            freq = falling.wobble_frequency if falling.wobble_frequency is not None else default_wobble_freq
            phase = falling.wobble_phase if falling.wobble_phase is not None else default_wobble_phase
            falling.stop_on_floor = stop  # normalize potential None

            # Apply gravity
            vel.vy += g * dt

            # Clamp downward speed
            if term > 0.0:
                if g >= 0.0:
                    vel.vy = min(vel.vy, term)
                else:
                    vel.vy = max(vel.vy, -term)

            # Horizontal wobble (sine), keeping velocity bounded by amplitude.
            if amp != 0.0 and freq != 0.0:
                falling.wobble_time += dt
                omega = 2.0 * math.pi * freq
                vel.vx = amp * math.sin(omega * falling.wobble_time + phase)
