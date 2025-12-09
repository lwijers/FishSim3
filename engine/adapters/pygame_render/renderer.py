# engine/adapters/pygame_render/renderer.py
from __future__ import annotations

import pygame
from engine.app.constants import DEFAULT_BG_COLOR


class Renderer:
    """
    Thin wrapper around the Pygame screen surface.
    Systems will use this via the ResourceStore, not via raw pygame calls.
    """

    def __init__(self, screen: pygame.Surface, bg_color=None) -> None:
        self.screen = screen
        self.bg_color = tuple(bg_color) if bg_color is not None else DEFAULT_BG_COLOR
        # Cache of scaled surfaces: {(id(image), target_size): scaled_surface}
        self._scale_cache: dict[tuple[int, tuple[int, int]], pygame.Surface] = {}

    def clear(self) -> None:
        """Fill the entire screen with the background color."""
        self.screen.fill(self.bg_color)

    def present(self) -> None:
        """Present the backbuffer to the display."""
        pygame.display.flip()

    def draw_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color,
        outline_width: int = 0,
    ) -> None:
        """
        Draw a rectangle given primitive values (no pygame.Rect in game layer).
        """
        rect = pygame.Rect(int(x), int(y), int(width), int(height))
        pygame.draw.rect(self.screen, color, rect, outline_width)

    def draw_image(
        self,
        image: pygame.Surface,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Draw a (possibly scaled) image at the given screen-space rect."""
        if width <= 0 or height <= 0:
            return

        target_size = (int(width), int(height))
        cache_key = (id(image), target_size)

        # Reuse scaled surfaces when possible to avoid per-frame allocations.
        if image.get_size() != target_size:
            cached = self._scale_cache.get(cache_key)
            if cached is None:
                cached = pygame.transform.smoothscale(image, target_size)
                self._scale_cache[cache_key] = cached
            image = cached

        self.screen.blit(image, (int(x), int(y)))
