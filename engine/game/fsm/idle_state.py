# engine/game/fsm/idle_state.py
from __future__ import annotations

import random
import math

from engine.ecs import EntityId, World
from engine.game.components.fish import Fish
from engine.game.components.brain import Brain
from engine.game.components.movement_intent import MovementIntent
from engine.game.components.bobbing import Bobbing
from engine.game.fsm.base_state import FishState


class IdleState(FishState):
    """
    Simple idle state:
      - On enter: zero movement, set a fixed duration.
      - Update: after duration, request transition to "cruise".
    """
    name = "idle"

    def __init__(self, duration_range, bob_amp_range=None, bob_freq_range=None) -> None:
        self._dur_range = duration_range
        self._bob_amp_range = bob_amp_range
        self._bob_freq_range = bob_freq_range

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
        intent.target_vx = 0.0
        intent.target_vy = 0.0
        if self._bob_amp_range and self._bob_freq_range:
            amp_lo, amp_hi = self._bob_amp_range
            freq_lo, freq_hi = self._bob_freq_range
            amp = rng.uniform(float(amp_lo), float(amp_hi))
            freq = rng.uniform(float(freq_lo), float(freq_hi))
            phase = rng.uniform(0.0, 2.0 * math.pi)
            world.add_component(eid, Bobbing(amplitude=amp, frequency=freq, phase=phase, t=0.0))

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
        # time_in_state is advanced by the FSM system before this call
        if brain.time_in_state >= brain.state_duration:
            return "cruise"
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
        world.remove_component(eid, Bobbing)
