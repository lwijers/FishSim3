# engine/ecs/commands.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

from .world import EntityId


@dataclass
class CreateEntityCmd:
    components: Iterable[Any]


@dataclass
class DestroyEntityCmd:
    entity: EntityId
