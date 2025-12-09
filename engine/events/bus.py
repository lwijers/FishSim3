# engine/events/bus.py
from __future__ import annotations

from typing import Callable, Dict, List, Type, Any


class EventBus:
    """
    Simple synchronous pub-sub event bus.

    Systems or adapters can:
      - subscribe(event_type, callback)
      - publish(event_instance)
    """

    def __init__(self) -> None:
        # {event_type: [callback]}
        self._subs: Dict[Type[Any], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[Any], callback: Callable[[Any], None]) -> None:
        self._subs.setdefault(event_type, []).append(callback)

    def publish(self, event: Any) -> None:
        callbacks = self._subs.get(type(event), [])
        for cb in callbacks:
            cb(event)
