# engine/adapters/pygame_render/app.py
from __future__ import annotations

import pygame

from engine.adapters.pygame_render.renderer import Renderer
from engine.app.constants import (
    FPS,
    DEFAULT_WINDOW_SIZE,
    DEFAULT_WINDOW_TITLE,
    DEFAULT_BG_COLOR,
)


class PygameApp:
    """
    Thin Pygame application wrapper.
    Responsibilities:
      - Initialize Pygame and create the window.
      - Attach a Renderer to the engine's ResourceStore.
      - Drive the main loop: poll events, call engine.update and engine.render.
      - Handle window resize and propagate new size to resources.
    """

    def __init__(
        self,
        engine,
        width: int | None = None,
        height: int | None = None,
        title: str | None = None,
    ) -> None:
        self.engine = engine

        default_w, default_h = DEFAULT_WINDOW_SIZE
        self.width = width if width is not None else default_w
        self.height = height if height is not None else default_h
        self.title = title if title is not None else DEFAULT_WINDOW_TITLE

        self._running = False

        # --- Pygame init & window creation ---
        pygame.init()
        # Make window resizable
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()

        # --- Attach Renderer + screen info as resources ---
        ui_cfg = self.engine.resources.try_get("ui_config", {})
        bg_color = tuple(
            ui_cfg.get("colors", {}).get("background", DEFAULT_BG_COLOR)
        )

        renderer = Renderer(self.screen, bg_color=bg_color)
        self.engine.resources.set("renderer", renderer)
        self.engine.resources.set("screen_size", (self.width, self.height))

    def _handle_resize(self, event: pygame.event.Event) -> None:
        """Handle VIDEORESIZE: recreate window, update renderer + resources."""
        self.width, self.height = event.size
        # Recreate the display surface with RESIZABLE flag
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE,
        )
        # Update renderer to draw to the new surface
        renderer: Renderer = self.engine.resources.get("renderer")
        renderer.screen = self.screen
        # Update screen_size resource so systems see the new size
        self.engine.resources.set("screen_size", (self.width, self.height))

    def run(self) -> None:
        """Main loop. ESC or window close will exit."""
        self._running = True
        while self._running:
            # Cap at FPS, get dt in seconds
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            # --- Event polling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.type == pygame.VIDEORESIZE:
                    # User resized the window
                    self._handle_resize(event)

            # --- Engine update & render ---
            self.engine.update(dt)
            self.engine.render(dt)

        pygame.quit()
