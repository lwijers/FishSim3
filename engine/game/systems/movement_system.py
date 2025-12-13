# engine/game/systems/movement_system.py
from __future__ import annotations
import math
import random
from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.game.components.position import Position
from engine.game.components.velocity import Velocity
from engine.game.components.rect_sprite import RectSprite
from engine.game.components.sprite_ref import SpriteRef
from engine.game.components.in_tank import InTank
from engine.game.components.tank_bounds import TankBounds
from engine.game.components.movement_intent import MovementIntent
from engine.game.components.falling import Falling


class MovementSystem(System):
    """
    Simple movement + bounce system.
    - Integrates position from velocity.
    - If a MovementIntent exists for an entity, it *drives* its Velocity:
        vel := intent.target_v (with acceleration cap if configured)
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

        move_cfg = resources.try_get("movement_config", {})

        # Basic movement caps
        max_accel = float(move_cfg.get("max_accel", 0.0))
        max_speed = float(move_cfg.get("max_speed", 0.0))

        # NEW: soft-brake config when approaching walls
        avoid_cfg = move_cfg.get("avoidance", {})
        #  - avoid_margin: how close to the wall we start braking (logical units)
        #  - avoid_brake_min_factor: minimum speed factor at the wall (0..1)
        avoid_margin = float(avoid_cfg.get("margin", 0.0))
        avoid_brake_min_factor = float(avoid_cfg.get("brake_min_factor", move_cfg.get("avoid_brake_min_factor", 0.3)))
        avoid_brake_min_factor = max(0.0, min(1.0, avoid_brake_min_factor))
        avoid_strength = float(avoid_cfg.get("strength", 0.0))

        # Redirect config when clamped
        redirect_cfg = move_cfg.get("redirect", {})
        redirect_min_speed = float(redirect_cfg.get("min_speed", 0.0))
        redirect_tangent_jitter = float(redirect_cfg.get("tangent_jitter", 0.0))
        rng_redirect: random.Random = resources.try_get("rng_ai", random.Random())

        # Component stores for tank bounds and intents
        in_tank_store = world.get_components(InTank)
        tank_bounds_store = world.get_components(TankBounds)
        intent_store = world.get_components(MovementIntent)
        falling_store = world.get_components(Falling)
        sprite_ref_store = world.get_components(SpriteRef)

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
                target_vx = intent.target_vx
                target_vy = intent.target_vy

                if max_accel > 0.0:
                    # Accelerate towards target velocity with a cap
                    dvx = target_vx - vel.vx
                    dvy = target_vy - vel.vy
                    # Limit magnitude of delta-v by max_accel * dt
                    max_dv = max_accel * dt
                    mag2 = dvx * dvx + dvy * dvy
                    if mag2 > 0.0:
                        mag = mag2 ** 0.5
                        if mag > max_dv > 0.0:
                            scale = max_dv / mag
                            dvx *= scale
                            dvy *= scale
                    vel.vx += dvx
                    vel.vy += dvy
                else:
                    # Hard snap to target velocity
                    vel.vx = target_vx
                    vel.vy = target_vy

            # ------------------------------------------------------------
            # 2) Determine movement bounds for this entity
            # ------------------------------------------------------------
            in_tank = in_tank_store.get(eid)
            if in_tank is not None:
                # Look up TankBounds for the tank id; fall back to full logical space
                t_bounds = tank_bounds_store.get(in_tank.tank)
                if t_bounds is not None:
                    left = t_bounds.x
                    top = t_bounds.y
                    right = t_bounds.x + t_bounds.width
                    bottom = t_bounds.y + t_bounds.height
                else:
                    left, top, right, bottom = 0.0, 0.0, float(logical_w), float(logical_h)
            else:
                # No tank: full logical area
                left, top, right, bottom = 0.0, 0.0, float(logical_w), float(logical_h)

            # Keep the *sprite* fully inside the bounds
            min_x = left
            max_x = right - sprite.width
            min_y = top
            max_y = bottom - sprite.height

            # ------------------------------------------------------------
            # 2b) SOFT BRAKING NEAR WALLS (ONLY FOR INTENT-DRIVEN ACTORS)
            # ------------------------------------------------------------
            # Idea:
            #   When a fish gets within 'avoid_margin' of *any* wall, scale down its
            #   velocity so it glides in rather than slamming and bouncing.
            #
            #   brake_factor goes from 1.0 (outside margin) down to
            #   avoid_brake_min_factor (at the wall).
            if intent is not None and avoid_margin > 0.0:
                # Distance from the *sprite origin* to each wall, in logical space
                dist_left = pos.x - min_x
                dist_right = max_x - pos.x
                dist_top = pos.y - min_y
                dist_bottom = max_y - pos.y

                # If we're *already* outside (can happen a frame after a big dt),
                # don't try to brake; the bounce logic will clean up.
                if (
                    dist_left >= 0.0
                    and dist_right >= 0.0
                    and dist_top >= 0.0
                    and dist_bottom >= 0.0
                ):
                    # Push inward when inside the margin
                    if avoid_strength > 0.0:
                        push_x = 0.0
                        push_y = 0.0
                        if dist_left < avoid_margin:
                            weight = 1.0 - dist_left / avoid_margin
                            push_x += avoid_strength * weight
                        if dist_right < avoid_margin:
                            weight = 1.0 - dist_right / avoid_margin
                            push_x -= avoid_strength * weight
                        if dist_top < avoid_margin:
                            weight = 1.0 - dist_top / avoid_margin
                            push_y += avoid_strength * weight
                        if dist_bottom < avoid_margin:
                            weight = 1.0 - dist_bottom / avoid_margin
                            push_y -= avoid_strength * weight
                        if max_accel > 0.0:
                            mag = math.hypot(push_x, push_y)
                            if mag > max_accel:
                                scale = max_accel / mag
                                push_x *= scale
                                push_y *= scale
                        vel.vx += push_x * dt
                        vel.vy += push_y * dt

                    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                    if min_dist < avoid_margin:
                        # 0 at wall, 1 at edge of margin
                        t = max(0.0, min_dist / avoid_margin)
                        # Lerp between [avoid_brake_min_factor, 1.0]
                        brake = (
                            avoid_brake_min_factor
                            + (1.0 - avoid_brake_min_factor) * t
                        )
                        vel.vx *= brake
                        vel.vy *= brake

            # ------------------------------------------------------------
            # 3) Clamp speed before integrating, then integrate position
            # ------------------------------------------------------------
            if max_speed > 0.0:
                speed2 = vel.vx * vel.vx + vel.vy * vel.vy
                max_speed2 = max_speed * max_speed
                if speed2 > max_speed2:
                    speed = speed2 ** 0.5
                    if speed > 0.0:
                        scale = max_speed / speed
                        vel.vx *= scale
                        vel.vy *= scale

            pos.x += vel.vx * dt
            pos.y += vel.vy * dt

            # ------------------------------------------------------------
            # 4) Boundary handling: clamp + redirect intent/velocity inward
            # ------------------------------------------------------------
            hit_left = pos.x < min_x
            hit_right = pos.x > max_x
            hit_top = pos.y < min_y
            hit_bottom = pos.y > max_y

            # Clamp position so we never drift outside
            if hit_left:
                pos.x = min_x
            elif hit_right:
                pos.x = max_x

            if hit_top:
                pos.y = min_y
            elif hit_bottom:
                pos.y = max_y

            if not (hit_left or hit_right or hit_top or hit_bottom):
                # Keep sprite facing the direction of travel when inside bounds.
                sprite_ref = sprite_ref_store.get(eid)
                if sprite_ref is not None and abs(vel.vx) > 1e-3:
                    sprite_ref.facing_left = vel.vx < 0.0
                continue

            if intent is None:
                # Legacy bounce for non-intent actors (pellets, etc.)
                if hit_left or hit_right:
                    vel.vx = -vel.vx
                if hit_top:
                    vel.vy = -vel.vy
                elif hit_bottom:
                    if falling is not None and falling.stop_on_floor:
                        vel.vx = 0.0
                        vel.vy = 0.0
                        falling.grounded = True
                    else:
                        vel.vy = -vel.vy
                continue

            # Redirect intent/velocity inward
            speed = math.hypot(vel.vx, vel.vy)
            if speed <= 1e-5:
                speed = 0.0
            if redirect_min_speed > 0.0:
                speed = max(speed, redirect_min_speed)

            dir_x = 0.0
            dir_y = 0.0
            if hit_left:
                dir_x = 1.0
            elif hit_right:
                dir_x = -1.0
            else:
                dir_x = math.copysign(1.0, vel.vx) if vel.vx != 0 else 0.0

            if hit_top:
                dir_y = 1.0
            elif hit_bottom:
                dir_y = -1.0
            else:
                dir_y = math.copysign(1.0, vel.vy) if vel.vy != 0 else 0.0

            # Tangential jitter to avoid sticking on axes
            if redirect_tangent_jitter > 0.0:
                jitter = redirect_tangent_jitter
                if hit_left or hit_right:
                    dir_y += rng_redirect.uniform(-jitter, jitter)
                if hit_top or hit_bottom:
                    dir_x += rng_redirect.uniform(-jitter, jitter)

            mag = math.hypot(dir_x, dir_y)
            if mag > 0:
                dir_x /= mag
                dir_y /= mag

            new_vx = dir_x * speed
            new_vy = dir_y * speed

            if hit_bottom and falling is not None and falling.stop_on_floor:
                new_vx = 0.0
                new_vy = 0.0
                falling.grounded = True

            vel.vx = new_vx
            vel.vy = new_vy
            intent.target_vx = new_vx
            intent.target_vy = new_vy
            # Redirect invalidates the old debug target; AI will pick a fresh one.

            sprite_ref = sprite_ref_store.get(eid)
            if sprite_ref is not None and abs(new_vx) > 1e-3:
                sprite_ref.facing_left = new_vx < 0.0
