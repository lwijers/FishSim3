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
            # If no rng_ai is provided, try to derive from rng_root so the
            # overall seed still controls everything; otherwise fall back
            # to a fixed seed.
            rng_root = resources.try_get("rng_root")
            if rng_root is not None:
                rng = random.Random(rng_root.randint(0, RNG_MAX_INT))
            else:
                rng = random.Random(RNG_ROOT_SEED)
            resources.set("rng_ai", rng)
        self._rng: random.Random = rng

        # Optional species config (for speed ranges)
        species_cfg = resources.try_get("species_config", {})

        # State registry
        self._states: Dict[str, object] = {
            "idle": IdleState(duration=self.IDLE_DURATION),
            "cruise": CruiseState(
                duration=self.CRUISE_DURATION,
                species_cfg=species_cfg,
                default_speed=self.DEFAULT_CRUISE_SPEED,
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

    def update(self, world: World, dt: float) -> None:
        for eid, fish, brain, intent in world.view(Fish, Brain, MovementIntent):
            if not brain.initialized:
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
