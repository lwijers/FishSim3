# engine/game/fsm/cruise_state.py
from __future__ import annotations

import math
import random
from typing import Dict, Tuple

from engine.ecs import World, EntityId
from engine.game.components import Fish, Brain, MovementIntent, Position, InTank, TankBounds

from .base_state import FishState
from .idle_state import _pick_weighted_next  # shared helper


class CruiseState(FishState):
    """
    'cruise' = wandering swim:
      - Picks a random target point inside the fish's tank (with an inner margin).
      - Moves toward that point at a species-driven speed.
      - Retargets when close; exits after the configured duration.
    """

    name = "cruise"

    def __init__(
        self,
        duration_range,
        species_cfg: Dict[str, Dict],
        default_speed: float,
        inner_margin: float = 40.0,
        fallback_radius: float = 60.0,
        retarget_min_distance: float = 5.0,
        retarget_distance_factor: float = 0.2,
        transition_weights=None,
        fallback_next: str = "idle",
    ) -> None:
        self._dur_min = float(duration_range[0])
        self._dur_max = float(duration_range[1])
        self._species_cfg = species_cfg or {}
        self._default_speed = float(default_speed)
        self._inner_margin = float(inner_margin)
        self._fallback_radius = float(fallback_radius)
        self._retarget_min_distance = float(retarget_min_distance)
        self._retarget_distance_factor = float(retarget_distance_factor)
        self._transition_weights = transition_weights or {}
        self._fallback_next = fallback_next

        # Per-fish targets & speeds while cruising
        self._targets: Dict[EntityId, Tuple[float, float]] = {}
        self._speeds: Dict[EntityId, float] = {}

    # --- Helpers -------------------------------------------------------------

    def _choose_duration(self, rng: random.Random) -> float:
        return rng.uniform(self._dur_min, self._dur_max)

    def _choose_speed(self, fish: Fish, rng: random.Random) -> float:
        spec = self._species_cfg.get(fish.species_id, {})
        speed_range = spec.get("speed_range")
        if isinstance(speed_range, (list, tuple)) and len(speed_range) >= 2:
            lo = float(speed_range[0])
            hi = float(speed_range[1])
            return rng.uniform(lo, hi)
        return self._default_speed

    def _pick_target_within_tank(
        self, world: World, eid: EntityId, pos: Position, rng: random.Random
    ) -> Tuple[float, float]:
        """
        Pick a random target point inside the fish's tank bounds, with a
        configurable margin from the walls. If we can't find tank bounds,
        pick a point in a small radius around the current position.
        """
        in_tank_store = world.get_components(InTank)
        tank_bounds_store = world.get_components(TankBounds)

        in_tank = in_tank_store.get(eid)
        bounds = None
        if in_tank is not None:
            bounds = tank_bounds_store.get(in_tank.tank)

        if bounds is not None:
            margin = self._inner_margin

            left = bounds.x + margin
            right = bounds.x + bounds.width - margin
            top = bounds.y + margin
            bottom = bounds.y + bounds.height - margin

            # Degenerate case: tank smaller than 2 * margin
            if right <= left or bottom <= top:
                tx = bounds.x + bounds.width * 0.5
                ty = bounds.y + bounds.height * 0.5
            else:
                tx = rng.uniform(left, right)
                ty = rng.uniform(top, bottom)
        else:
            # Fallback: random point in a small disk around current position
            radius = self._fallback_radius
            angle = rng.uniform(0.0, math.tau)
            r = rng.uniform(0.0, radius)
            tx = pos.x + math.cos(angle) * r
            ty = pos.y + math.sin(angle) * r

        return tx, ty

    def _ensure_intent(self, world: World, eid: EntityId, intent: MovementIntent) -> MovementIntent:
        if intent is None:
            intent = MovementIntent()
            world.add_component(eid, intent)
        return intent

    # --- State interface -----------------------------------------------------

    def on_enter(
        self,
        eid: EntityId,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
        rng: random.Random,
    ) -> None:
        brain.time_in_state = 0.0
        brain.state_duration = self._choose_duration(rng)

        speed = self._choose_speed(fish, rng)
        self._speeds[eid] = speed

        pos_store = world.get_components(Position)
        pos = pos_store.get(eid)
        if pos is None:
            # No position? Just pick a random heading.
            angle = rng.uniform(0.0, math.tau)
            intent.target_vx = math.cos(angle) * speed
            intent.target_vy = math.sin(angle) * speed
            return

        tx, ty = self._pick_target_within_tank(world, eid, pos, rng)
        self._targets[eid] = (tx, ty)
        intent.debug_target = (tx, ty)

        # Immediately set intent toward the first target
        dx = tx - pos.x
        dy = ty - pos.y
        dist = math.hypot(dx, dy)
        if dist > 1e-4:
            dir_x = dx / dist
            dir_y = dy / dist
            intent.target_vx = dir_x * speed
            intent.target_vy = dir_y * speed
        else:
            intent.target_vx = 0.0
            intent.target_vy = 0.0

    def update(
        self,
        eid: EntityId,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
        dt: float,
        rng: random.Random,
    ) -> str | None:
        # Transition out when cruise duration is over
        if brain.time_in_state >= brain.state_duration:
            return _pick_weighted_next(self._transition_weights, rng, self._fallback_next)

        pos_store = world.get_components(Position)
        pos = pos_store.get(eid)
        if pos is None:
            return None

        intent = self._ensure_intent(world, eid, intent)

        # Ensure we have a target and speed for this fish
        target = self._targets.get(eid)
        if target is None:
            target = self._pick_target_within_tank(world, eid, pos, rng)
            self._targets[eid] = target

        speed = self._speeds.get(eid)
        if speed is None:
            speed = self._choose_speed(fish, rng)
            self._speeds[eid] = speed

        tx, ty = target
        dx = tx - pos.x
        dy = ty - pos.y
        dist = math.hypot(dx, dy)

        # How close is "close enough" to retarget?
        close_dist = max(self._retarget_min_distance, speed * self._retarget_distance_factor)

        if dist <= close_dist:
            # Reached target: pick a new one inside bounds
            tx, ty = self._pick_target_within_tank(world, eid, pos, rng)
            self._targets[eid] = (tx, ty)
            intent.debug_target = (tx, ty)
            dx = tx - pos.x
            dy = ty - pos.y
            dist = math.hypot(dx, dy)
        else:
            intent.debug_target = (tx, ty)

        if dist > 1e-4:
            dir_x = dx / dist
            dir_y = dy / dist
            intent.target_vx = dir_x * speed
            intent.target_vy = dir_y * speed
        else:
            intent.target_vx = 0.0
            intent.target_vy = 0.0

        return None

    def on_exit(
        self,
        eid: EntityId,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
        rng: random.Random,
    ) -> None:
        # Cleanup per-entity state so we pick fresh targets/speeds next time.
        self._targets.pop(eid, None)
        self._speeds.pop(eid, None)
        intent.debug_target = None
