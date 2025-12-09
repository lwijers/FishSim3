# engine/ecs/view.py
from __future__ import annotations

from typing import Iterable, Tuple, Type, Any, Iterator

from .world import World, EntityId


class View:
    """
    Iterable *and* iterator over entities that have a given set of component types.

    Example:
        for eid, pos, vel in world.view(Position, Velocity):
            ...

        eid, pos = next(world.view(Position))
    """

    def __init__(self, world: World, component_types: Iterable[Type[Any]]) -> None:
        self._world = world
        self._component_types: Tuple[Type[Any], ...] = tuple(component_types)
        self._gen: Iterator[Any] | None = None  # underlying iterator for this pass

    # ------------------------------------------------------------------
    # Iterator protocol
    # ------------------------------------------------------------------
    def __iter__(self) -> "View":
        """
        Called when you do: for ... in view
        Resets the internal generator for a fresh iteration.
        """
        self._gen = self._iter_impl()
        return self

    def __next__(self):
        """
        Called when you do: next(view)
        If no generator yet (e.g. user called next(view) without iter(view)),
        create one on the fly.
        """
        if self._gen is None:
            self._gen = self._iter_impl()
        return next(self._gen)

    # ------------------------------------------------------------------
    # Internal iterator builder
    # ------------------------------------------------------------------
    def _iter_impl(self) -> Iterator[Any]:
        """
        Build a fresh iterator over (eid, comp1, comp2, ...).

        We compute the intersection of entity ids that have all components.
        """
        if not self._component_types:
            # No components requested: empty iterator
            return iter(())

        world = self._world
        first_type, *rest_types = self._component_types

        # We capture base_store here; it's fine if world mutates later,
        # because a new iteration will build a new generator.
        base_store = world.get_components(first_type)

        def generator() -> Iterator[Any]:
            for eid, first_comp in base_store.items():
                comps = [first_comp]
                missing = False
                for ctype in rest_types:
                    store = world.get_components(ctype)
                    comp = store.get(eid)
                    if comp is None:
                        missing = True
                        break
                    comps.append(comp)

                if not missing:
                    # (eid, c1, c2, ...)
                    yield (EntityId(eid), *comps)

        return generator()
