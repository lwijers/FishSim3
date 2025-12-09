# engine/ecs/commands.py
from dataclasses import dataclass
from typing import Dict, Type, Any

# Simple alias so we don't create circular imports.
# World can also define EntityId = int; they don't need to be literally the same object.
EntityId = int


@dataclass
class CreateEntityCmd:
    """
    Request to create a new entity with a given component set.

    components:
        dict mapping ComponentType -> component instance
        e.g. {Position: Position(...), Velocity: Velocity(...)}
    """
    components: Dict[Type[Any], Any]


@dataclass
class DestroyEntityCmd:
    """
    Request to destroy the given entity id.
    """
    entity_id: EntityId
