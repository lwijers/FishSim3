from __future__ import annotations
from typing import Optional, Tuple

import pygame

from engine.app.constants import FALLBACK_SCREEN_SIZE
from engine.resources import ResourceStore
from engine.game.events.input_events import ClickWorld, ClickUI, Scroll, PointerMove

class InputAdapter:
    """
    Converts raw Pygame events into domain events on the EventBus.
    Handles letterboxed logical-to-screen mapping (inverse of render).
    """

    def __init__(self, resources: ResourceStore) -> None:
        self.resources = resources
        self.bus = resources.get("events")

    def _to_logical(self, screen_pos: Tuple[int, int]) -> Optional[Tuple[float, float]]:
        mx, my = screen_pos
        screen_w, screen_h = self.resources.try_get("screen_size", FALLBACK_SCREEN_SIZE)
        logical_w, logical_h = self.resources.try_get("logical_size", (screen_w, screen_h))
        if logical_w <= 0 or logical_h <= 0:
            logical_w, logical_h = screen_w, screen_h

        scale_x = screen_w / logical_w
        scale_y = screen_h / logical_h
        scale = min(scale_x, scale_y)
        if scale <= 0:
            return None

        render_w = logical_w * scale
        render_h = logical_h * scale
        offset_x = (screen_w - render_w) / 2.0
        offset_y = (screen_h - render_h) / 2.0

        if mx < offset_x or mx > offset_x + render_w or my < offset_y or my > offset_y + render_h:
            return None

        lx = (mx - offset_x) / scale
        ly = (my - offset_y) / scale
        return float(lx), float(ly)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 2, 3):  # left/middle/right
                logical = self._to_logical(event.pos)
                if logical:
                    x, y = logical
                    self.bus.publish(ClickWorld(x=x, y=y, button=event.button))
            elif event.button in (4, 5):  # wheel
                delta = 1.0 if event.button == 4 else -1.0
                self.bus.publish(Scroll(delta=delta))
        elif event.type == pygame.MOUSEWHEEL:
            self.bus.publish(Scroll(delta=float(event.y)))
        elif event.type == pygame.MOUSEMOTION:
            logical = self._to_logical(event.pos)
            if logical:
                x, y = logical
                self.bus.publish(PointerMove(x=x, y=y))
