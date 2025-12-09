# engine/ecs/system.py
from __future__ import annotations

from typing import Any, Dict, Set


class System:
    """
    Base class for all systems.

    - Each system belongs to a phase (pre_update / logic / post_update / render).
    - Systems receive a resources object (ResourceStore or similar).
    """

    # Default phase; subclasses should override.
    phase: str = "logic"

    def __init__(self, resources: Any) -> None:
        self.resources = resources

    def declare_requirements(self) -> Dict[str, Set[Any]]:
        """
        Optional: describe which components/resources this system needs.

        Not used by the MVP scheduler, but useful later for diagnostics,
        tooling, or automatic ordering.
        """
        return {}

    def update(self, world, dt: float) -> None:
        """Perform one frame of work."""
        raise NotImplementedError("System.update must be implemented by subclasses")
