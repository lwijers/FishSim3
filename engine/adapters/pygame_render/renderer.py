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
