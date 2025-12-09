# engine/scheduling/scheduler.py
from __future__ import annotations

from typing import Dict, List

from engine.ecs import System, World


class Scheduler:
    """
    Very simple phase-based scheduler.

    Phases:
      - pre_update: input, time step updates, housekeeping
      - logic: gameplay, AI, physics
      - post_update: apply queued commands, cleanup, sync
      - render: draw the current state
    """

    def __init__(self) -> None:
        self._systems_by_phase: Dict[str, List[System]] = {
            "pre_update": [],
            "logic": [],
            "post_update": [],
            "render": [],
        }

    def add_system(self, system: System, phase: str | None = None) -> None:
        """
        Register a system for a given phase.
        If phase is None, system.phase is used.
        """
        ph = phase or getattr(system, "phase", "logic")
        if ph not in self._systems_by_phase:
            raise ValueError(f"Unknown phase: {ph!r}")
        self._systems_by_phase[ph].append(system)

    # ------------------------------------------------------------------
    # Update & render loops
    # ------------------------------------------------------------------
    def update(self, world: World, dt: float) -> None:
        # pre_update, logic, post_update
        for phase in ("pre_update", "logic", "post_update"):
            for sys in self._systems_by_phase[phase]:
                sys.update(world, dt)

            # After post_update, we want to apply entity commands
            if phase == "post_update":
                world.flush_commands()

    def render(self, world: World, dt: float) -> None:
        for sys in self._systems_by_phase["render"]:
            sys.update(world, dt)
