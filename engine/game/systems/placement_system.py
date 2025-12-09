from __future__ import annotations
from typing import List, Tuple
from engine.ecs import System, World
from engine.ecs.commands import CreateEntityCmd
from engine.resources import ResourceStore
from engine.game.components import Position, RectSprite, InTank, TankBounds, Tank
from engine.game.components.pellet import Pellet
from engine.game.events.input_events import ClickWorld
from engine.game.factories.pellet_factory import create_pellet_cmd, DEFAULT_PELLET_SIZE

class PlacementSystem(System):
    """Listens for ClickWorld events and queues pellet creation inside tanks."""
    phase = "logic"

    def __init__(self, resources: ResourceStore) -> None:
        super().__init__(resources)
        self._pending: List[ClickWorld] = []
        bus = resources.get("events")
        bus.subscribe(ClickWorld, self._on_click)

    def _on_click(self, event: ClickWorld) -> None:
        self._pending.append(event)

    def _find_tank_at(self, world: World, x: float, y: float) -> Tuple[int | None, TankBounds | None]:
        for eid, tank, bounds in world.view(Tank, TankBounds):
            if bounds.x <= x <= bounds.x + bounds.width and bounds.y <= y <= bounds.y + bounds.height:
                return eid, bounds
        return None, None

    def update(self, world: World, dt: float) -> None:
        if not self._pending:
            return

        events = self._pending
        self._pending = []

        for evt in events:
            tank_eid, bounds = self._find_tank_at(world, evt.x, evt.y)
            if tank_eid is None or bounds is None:
                continue

            size = DEFAULT_PELLET_SIZE
            clamped_x = max(bounds.x, min(evt.x, bounds.x + bounds.width - size))
            clamped_y = max(bounds.y, min(evt.y, bounds.y + bounds.height - size))

            cmd: CreateEntityCmd = create_pellet_cmd(clamped_x, clamped_y, tank_eid, size=size)
            world.queue_command(cmd)
