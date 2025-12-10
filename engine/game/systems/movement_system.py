# engine/game/systems/movement_system.py
from __future__ import annotations
from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components.position import Position
from engine.game.components.velocity import Velocity
from engine.game.components.rect_sprite import RectSprite
from engine.game.components.in_tank import InTank
from engine.game.components.tank_bounds import TankBounds
from engine.game.components.movement_intent import MovementIntent
from engine.game.components.falling import Falling
from engine.game.components.bobbing import Bobbing
import math


class MovementSystem(System):
    """
    Simple movement + bounce system.

    - Integrates position from velocity.
    - If a MovementIntent exists for an entity, it *drives* its Velocity:
        vel := intent.target_v
    - Bounces rectangles off the *tank bounds* if available (logical space).
    - Falls back to full *logical* bounds when the entity is not in a tank
      or the tank has no TankBounds.

    Note: logical space is independent of the actual window size.
    Rendering scales logical → screen; movement always works in logical units.
    """
    phase = "logic"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]

        # Logical game-space size:
        #  - prefer explicit logical_size
        #  - fall back to screen_size
        #  - finally fall back to a constant
        logical_w, logical_h = resources.try_get(
            "logical_size",
            resources.try_get("screen_size", FALLBACK_SCREEN_SIZE),
        )

        # Component stores for tank bounds and intents
        in_tank_store = world.get_components(InTank)
        tank_bounds_store = world.get_components(TankBounds)
        intent_store = world.get_components(MovementIntent)
        falling_store = world.get_components(Falling)
        bob_store = world.get_components(Bobbing)

        for eid, pos, vel, sprite in world.view(Position, Velocity, RectSprite):
            falling = falling_store.get(eid)
            if falling is not None and falling.stop_on_floor and falling.grounded:
                # Already landed: freeze motion.
                vel.vx = 0.0
                vel.vy = 0.0
                continue

            # ------------------------------------------------------------
            # 1) Apply MovementIntent (if present) to velocity
            # ------------------------------------------------------------
            intent = intent_store.get(eid)
            if intent is not None:
                vel.vx = intent.target_vx
                vel.vy = intent.target_vy

            bob = bob_store.get(eid)
            if bob is not None:
                bob.t += dt
                vel.vy += bob.amplitude * math.sin(2.0 * math.pi * bob.frequency * bob.t + bob.phase)

            # ------------------------------------------------------------
            # 2) Determine which bounds apply: tank bounds or full logical
            # ------------------------------------------------------------
            bounds = None
            in_tank = in_tank_store.get(eid)
            if in_tank is not None:
                bounds = tank_bounds_store.get(in_tank.tank)

            if bounds is not None:
                # Use the tank's rectangle (logical coords)
                left = float(bounds.x)
                top = float(bounds.y)
                right = float(bounds.x + bounds.width)
                bottom = float(bounds.y + bounds.height)
            else:
                # No tank / no TankBounds: fall back to full logical area
                left = 0.0
                top = 0.0
                right = float(logical_w)
                bottom = float(logical_h)

            # Effective motion bounds for the *top-left* of the sprite
            min_x = left
            max_x = right - sprite.width
            min_y = top
            max_y = bottom - sprite.height

            # ------------------------------------------------------------
            # 3) Integrate position
            # ------------------------------------------------------------
            pos.x += vel.vx * dt
            pos.y += vel.vy * dt

            # ------------------------------------------------------------
            # 4) Bounce against bounds
            # ------------------------------------------------------------
            # Horizontal
            if pos.x < min_x:
                pos.x = min_x
                vel.vx = -vel.vx
            elif pos.x > max_x:
                pos.x = max_x
                vel.vx = -vel.vx

            # Vertical
            if pos.y < min_y:
                pos.y = min_y
                vel.vy = -vel.vy
            elif pos.y > max_y:
                pos.y = max_y
                if falling is not None and falling.stop_on_floor:
                    vel.vy = 0.0
                    vel.vx = 0.0
                    falling.grounded = True
                else:
                    vel.vy = -vel.vy
