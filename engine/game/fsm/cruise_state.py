# engine/game/fsm/cruise_state.py
from __future__ import annotations

import math
import random
from typing import Dict, Any

from engine.ecs import EntityId, World
from engine.game.components.fish import Fish
from engine.game.components.brain import Brain
from engine.game.components.movement_intent import MovementIntent
from engine.game.fsm.base_state import FishState


class CruiseState(FishState):
    """
    Cruise state:
      - On enter: pick a random direction and speed (from species config if
        available) and set MovementIntent.
      - Update: after duration, request transition back to "idle".
    """
    name = "cruise"

    def __init__(
        self,
        duration_range,
        species_cfg: Dict[str, Dict[str, Any]] | None,
        default_speed: float,
    ) -> None:
        self._dur_range = duration_range
        self._species_cfg = species_cfg or {}
        self._default_speed = float(default_speed)

    def _pick_speed(self, fish: Fish, rng: random.Random) -> float:
        spec = self._species_cfg.get(fish.species_id)
        if spec is None:
            return self._default_speed

        speed_range = spec.get("speed_range")
        if (
            isinstance(speed_range, (list, tuple))
            and len(speed_range) == 2
        ):
            lo, hi = float(speed_range[0]), float(speed_range[1])
            return rng.uniform(lo, hi)

        return self._default_speed

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
        lo, hi = self._dur_range if isinstance(self._dur_range, (list, tuple)) else (self._dur_range, self._dur_range)
        brain.state_duration = rng.uniform(float(lo), float(hi))

        speed = self._pick_speed(fish, rng)
        angle = rng.uniform(0.0, 2.0 * math.pi)

        intent.target_vx = speed * math.cos(angle)
        intent.target_vy = speed * math.sin(angle)

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
        if brain.time_in_state >= brain.state_duration:
            return "idle"
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
        # Nothing special on exit (for now).
        pass
