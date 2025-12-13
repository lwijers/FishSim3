# engine/adapters/pygame_render/renderer.py
from __future__ import annotations

import pygame
from engine.app.constants import DEFAULT_BG_COLOR
from pathlib import Path


class Renderer:
    """
    Thin wrapper around the Pygame screen surface.
    Systems will use this via the ResourceStore, not via raw pygame calls.
    """

    def __init__(self, screen: pygame.Surface, bg_color=None) -> None:
        self.screen = screen
        self.bg_color = tuple(bg_color) if bg_color is not None else DEFAULT_BG_COLOR
        # Cache of transformed surfaces: {(id(image), target_size, flip_x): surface}
        self._scale_cache: dict[tuple[int, tuple[int, int], bool], pygame.Surface] = {}
        self._font_cache: dict[tuple[int, str], pygame.font.Font] = {}

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
        border_radius: int = 0,
    ) -> None:
        """
        Draw a rectangle given primitive values (no pygame.Rect in game layer).
        Supports outline + rounded corners via border_radius.
        """
        rect = pygame.Rect(int(x), int(y), int(width), int(height))
        pygame.draw.rect(self.screen, color, rect, outline_width, border_radius=border_radius)

    def draw_image(
        self,
        image: pygame.Surface,
        x: float,
        y: float,
        width: float,
        height: float,
        flip_x: bool = False,
    ) -> None:
        """Draw a (possibly scaled/flipped) image at the given screen-space rect."""
        if width <= 0 or height <= 0:
            return

        target_size = (int(width), int(height))
        cache_key = (id(image), target_size, bool(flip_x))

        # Reuse transformed surfaces when possible to avoid per-frame allocations.
        needs_transform = image.get_size() != target_size or flip_x
        if needs_transform:
            cached = self._scale_cache.get(cache_key)
            if cached is None:
                cached = image
                if image.get_size() != target_size:
                    cached = pygame.transform.smoothscale(image, target_size)
                if flip_x:
                    cached = pygame.transform.flip(cached, True, False)
                self._scale_cache[cache_key] = cached
            image = cached

        self.screen.blit(image, (int(x), int(y)))

    def draw_text(self, text: str, x: float, y: float, color=(255, 255, 255), font_size: int = 16, font_name: str | None = None) -> None:
        font_path: str | None = None
        if font_name:
            p = Path(font_name)
            if not p.is_absolute():
                p = Path("assets") / p
            if p.exists():
                font_path = str(p)

        key = (font_size, font_path or font_name or "")
        font = self._font_cache.get(key)
        if font is None:
            if font_path:
                font = pygame.font.Font(font_path, font_size)
            else:
                font = pygame.font.SysFont(font_name, font_size)
            self._font_cache[key] = font
        surface = font.render(text, True, color)
        self.screen.blit(surface, (int(x), int(y)))

    def draw_line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color=(255, 255, 255),
        width: int = 1,
    ) -> None:
        pygame.draw.line(self.screen, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), width)
