# engine/game/fsm/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
import random

from engine.ecs import EntityId, World
from engine.game.components.fish import Fish
from engine.game.components.brain import Brain
from engine.game.components.movement_intent import MovementIntent


class FishState(ABC):
    """
    Abstract base class for all fish FSM states.

    Each state must implement:
      - name (str): unique identifier ("idle", "cruise", ...)
      - on_enter(...)
      - update(...) -> next state name or None
      - on_exit(...)
    """

    #: Human-/debug-readable state name. Must be unique per state type.
    name: str

    @abstractmethod
    def on_enter(
        self,
        eid: EntityId,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
        rng: random.Random,
    ) -> None:
        """
        Called exactly once when entering this state.

        Should:
          - initialise timers on Brain (time_in_state, state_duration)
          - set up initial MovementIntent, if relevant
        """
        raise NotImplementedError

    @abstractmethod
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
        """
        Called every frame while in this state.

        Should:
          - read/modify Brain + Intent as needed
          - return:
              * None         -> stay in current state
              * state_name   -> request transition to a different state
        """
        raise NotImplementedError

    @abstractmethod
    def on_exit(
        self,
        eid: EntityId,
        world: World,
        fish: Fish,
        brain: Brain,
        intent: MovementIntent,
        rng: random.Random,
    ) -> None:
        """
        Called once right before leaving this state.

        Use this for cleanup / bookkeeping if needed.
        """
        raise NotImplementedError
