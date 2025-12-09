# engine/ecs/world.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Type, TypeVar, Iterable, Tuple, List, Any

from .commands import CreateEntityCmd, DestroyEntityCmd


class EntityId(int):
    """Opaque identifier for an entity in the world."""
    pass


TComponent = TypeVar("TComponent")


class World:
    """
    Minimal ECS World:
    - Generates entity IDs
    - Stores components grouped by type
    - Provides basic views over entities with given component sets
    - Has a simple command queue for create/destroy operations
    """

    def __init__(self) -> None:
        self._next_id: int = 1
        # {ComponentType: {EntityId: component_instance}}
        self._components: Dict[Type[Any], Dict[EntityId, Any]] = {}
        # Cache for views by component type tuple
        # (string annotation to avoid importing View at module import time)
        self._views: Dict[Tuple[Type[Any], ...], "View"] = {}
        # Deferred commands like CreateEntityCmd / DestroyEntityCmd
        self._command_queue: List[Any] = []

    # ------------------------------------------------------------------
    # Entity management
    # ------------------------------------------------------------------
    def create_entity(self) -> EntityId:
        eid = EntityId(self._next_id)
        self._next_id += 1
        return eid

    def destroy_entity(self, eid: EntityId) -> None:
        """Remove the entity from all component stores."""
        for comp_dict in self._components.values():
            comp_dict.pop(eid, None)

    # ------------------------------------------------------------------
    # Component management
    # ------------------------------------------------------------------
    def add_component(self, eid: EntityId, component: Any) -> None:
        ctype = type(component)
        store = self._components.setdefault(ctype, {})
        store[eid] = component
        self._invalidate_views_involving(ctype)

    def remove_component(self, eid: EntityId, component_type: Type[Any]) -> None:
        store = self._components.get(component_type)
        if store is not None and eid in store:
            del store[eid]
            self._invalidate_views_involving(component_type)

    def get_components(self, component_type: Type[TComponent]) -> Dict[EntityId, TComponent]:
        """Direct access to the raw dict for a single component type."""
        return self._components.setdefault(component_type, {})

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------
    def view(self, *component_types: Type[Any]) -> "View":
        """
        Return a View over all entities that have *all* the given components.
        Usage:
            for eid, pos, vel in world.view(Position, Velocity):
                ...
        """
        # LOCAL import to avoid circular import at module load time
        from .view import View

        key = tuple(component_types)
        view = self._views.get(key)
        if view is None:
            view = View(self, component_types)
            self._views[key] = view
        return view

    def _invalidate_views_involving(self, component_type: Type[Any]) -> None:
        """Drop cached views that depend on the given component type."""
        to_delete = [
            key for key in self._views.keys()
            if component_type in key
        ]
        for key in to_delete:
            del self._views[key]

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def queue_command(self, cmd: Any) -> None:
        """Queue a command to be applied later (CreateEntityCmd, DestroyEntityCmd)."""
        self._command_queue.append(cmd)

    def flush_commands(self) -> None:
        """Apply all queued commands (create/destroy entities).

        This should be called exactly once per frame by the Scheduler,
        typically after the 'post_update' phase.
        """
        while self._command_queue:
            cmd = self._command_queue.pop(0)
            if isinstance(cmd, CreateEntityCmd):
                self._apply_create_entity(cmd)
            elif isinstance(cmd, DestroyEntityCmd):
                # canonical field name is 'entity_id'
                self.destroy_entity(EntityId(cmd.entity_id))
            else:
                raise TypeError(f"Unknown command type: {type(cmd)!r}")

    def _apply_create_entity(self, cmd: CreateEntityCmd) -> EntityId:
        """Create a new entity and attach all components from cmd.components.

        cmd.components is a dict: {ComponentType: component_instance}.
        We only care about the component instances; add_component() infers
        the type from each instance.
        """
        eid = self.create_entity()
        for component in cmd.components.values():
            self.add_component(eid, component)
        return eid
