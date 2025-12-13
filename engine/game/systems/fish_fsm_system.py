# engine/game/systems/fish_fsm_system.py
from __future__ import annotations

import random
from typing import Dict

from engine.ecs import System, World
from engine.resources import ResourceStore
from engine.game.components import Fish, Brain, MovementIntent
from engine.game.fsm.idle_state import IdleState
from engine.game.fsm.cruise_state import CruiseState
from engine.app.constants import (
    FSM_IDLE_DURATION,
    FSM_CRUISE_DURATION,
    FSM_DEFAULT_CRUISE_SPEED,
    FSM_CRUISE_INNER_MARGIN,
    FSM_CRUISE_FALLBACK_RADIUS,
    FSM_CRUISE_RETARGET_MIN_DISTANCE,
    FSM_CRUISE_RETARGET_DISTANCE_FACTOR,
    RNG_ROOT_SEED,
    RNG_MAX_INT,
)


class FishFSMSystem(System):
    """
    Full FSM driver for fish movement.
    - Uses Brain to track current state and timing.
    - Uses MovementIntent as the output of the AI.
    - Implements state enter / in / exit semantics via state objects.
    """
    phase = "logic"

    # Defaults are defined in constants so there's a single source of truth.
    IDLE_DURATION: float = FSM_IDLE_DURATION
    CRUISE_DURATION: float = FSM_CRUISE_DURATION
    DEFAULT_CRUISE_SPEED: float = FSM_DEFAULT_CRUISE_SPEED

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)

        # Deterministic RNG for AI
        rng = resources.try_get("rng_ai")
        if rng is None:
            rng_root = resources.try_get("rng_root")
            if rng_root is not None:
                rng = random.Random(rng_root.randint(0, RNG_MAX_INT))
            else:
                rng = random.Random(RNG_ROOT_SEED)
            resources.set("rng_ai", rng)
        self._rng: random.Random = rng

        # Configurable ranges/weights
        fsm_cfg = resources.try_get("fsm_config", {})
        self._start_weights = fsm_cfg.get("start_state_weights", {"idle": 0.5, "cruise": 0.5})
        idle_range = fsm_cfg.get("idle_duration_range", [self.IDLE_DURATION, self.IDLE_DURATION])
        cruise_range = fsm_cfg.get("cruise_duration_range", [self.CRUISE_DURATION, self.CRUISE_DURATION])
        cruise_inner_margin = float(fsm_cfg.get("cruise_inner_margin", FSM_CRUISE_INNER_MARGIN))
        cruise_fallback_radius = float(fsm_cfg.get("cruise_fallback_radius", FSM_CRUISE_FALLBACK_RADIUS))
        cruise_retarget_min_distance = float(
            fsm_cfg.get("cruise_retarget_min_distance", FSM_CRUISE_RETARGET_MIN_DISTANCE)
        )
        cruise_retarget_distance_factor = float(
            fsm_cfg.get("cruise_retarget_distance_factor", FSM_CRUISE_RETARGET_DISTANCE_FACTOR)
        )
        transition_weights = fsm_cfg.get("transition_weights", {})
        idle_transitions = transition_weights.get("idle") if isinstance(transition_weights, dict) else None
        cruise_transitions = transition_weights.get("cruise") if isinstance(transition_weights, dict) else None

        # Optional species config (for speed ranges)
        species_cfg = resources.try_get("species_config", {})

        # State registry
        self._states: Dict[str, object] = {
            "idle": IdleState(duration_range=idle_range, transition_weights=idle_transitions, fallback_next="cruise"),
            "cruise": CruiseState(
                duration_range=cruise_range,
                species_cfg=species_cfg,
                default_speed=self.DEFAULT_CRUISE_SPEED,
                inner_margin=cruise_inner_margin,
                fallback_radius=cruise_fallback_radius,
                retarget_min_distance=cruise_retarget_min_distance,
                retarget_distance_factor=cruise_retarget_distance_factor,
                transition_weights=cruise_transitions,
                fallback_next="idle",
            ),
        }

    def _enter_state(
        self,
        eid,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
    ) -> None:
        """Call on_enter on whatever brain.state currently is."""
        state = self._states.get(brain.state)
        if state is None:
            # Fallback to idle if state name is unknown
            brain.state = "idle"
            state = self._states["idle"]
        state.on_enter(eid, world, fish, brain, intent, self._rng)

    def _pick_start_state(self) -> str:
        weights = []
        names = []
        for name, w in self._start_weights.items():
            names.append(name)
            weights.append(float(w))
        if not names:
            return "idle"
        total = sum(weights)
        if total <= 0:
            return names[0]
        r = self._rng.uniform(0, total)
        acc = 0.0
        for name, w in zip(names, weights):
            acc += w
            if r <= acc:
                return name
        return names[-1]

    def update(self, world: World, dt: float) -> None:
        for eid, fish, brain, intent in world.view(Fish, Brain, MovementIntent):
            if not brain.initialized:
                brain.state = self._pick_start_state()
                self._enter_state(eid, world, fish, brain, intent)
                brain.initialized = True

            brain.time_in_state += dt

            state = self._states.get(brain.state)
            if state is None:
                brain.state = "idle"
                state = self._states["idle"]

            next_state_name = state.update(
                eid, world, fish, brain, intent, dt, self._rng
            )

            if not next_state_name or next_state_name == brain.state:
                continue

            # Exit current state
            state.on_exit(eid, world, fish, brain, intent, self._rng)

            # Switch to next
            brain.state = next_state_name
            brain.time_in_state = 0.0
            brain.state_duration = 0.0

            new_state = self._states.get(next_state_name)
            if new_state is None:
                brain.state = "idle"
                new_state = self._states["idle"]
            new_state.on_enter(eid, world, fish, brain, intent, self._rng)
