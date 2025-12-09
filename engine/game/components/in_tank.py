# engine/game/components/in_tank.py
from dataclasses import dataclass
from engine.ecs import EntityId

@dataclass
class InTank:
    """
    Links an entity (fish, pellet, plant, etc.) to a specific tank entity.
    This lets systems operate per tank without global state.
    """
    tank: EntityId
