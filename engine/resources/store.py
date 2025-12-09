# engine/resources/store.py
from __future__ import annotations

from typing import Any, Dict


class ResourceStore:
    """
    Simple registry for globally accessible singletons:
      - config
      - rng
      - assets
      - audio
      - time
      - screen info
      - event bus, etc.
    """

    def __init__(self) -> None:
        self._items: Dict[str, Any] = {}

    def register(self, key: str, value: Any) -> None:
        if key in self._items:
            raise KeyError(f"Resource {key!r} is already registered")
        self._items[key] = value

    def set(self, key: str, value: Any) -> None:
        """Replace or create a resource without complaining."""
        self._items[key] = value

    def get(self, key: str) -> Any:
        return self._items[key]

    def try_get(self, key: str, default: Any = None) -> Any:
        return self._items.get(key, default)
