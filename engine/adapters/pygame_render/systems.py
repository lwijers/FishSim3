# adapters/pygame_render/systems.py
from __future__ import annotations

from engine.ecs import System, World
from engine.resources import ResourceStore


class ClearScreenSystem(System):
    """
    Render-phase system that clears the screen and presents it.

    For now this just gives us a visible background color so we can
    verify the PygameApp + engine loop is working.
    """

    phase = "render"

    def update(self, world: World, dt: float) -> None:
        resources: ResourceStore = self.resources  # type: ignore[assignment]
        renderer = resources.try_get("renderer")
        if renderer is None:
            # Renderer is not attached yet: nothing to do.
            return

        renderer.clear()
        renderer.present()
