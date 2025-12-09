# engine/adapters/pygame_render/app.py
from __future__ import annotations

from pathlib import Path

import pygame

from engine.adapters.pygame_render.renderer import Renderer
from engine.adapters.asset_loader import Assets
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
      - Initialize pygame + window
      - Hook Renderer + screen_size into the engine resources
      - Run the main loop and forward dt to engine.update/render
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
        self.width = int(width or default_w)
        self.height = int(height or default_h)
        self.title = title or DEFAULT_WINDOW_TITLE

        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self._running: bool = False

        self._init_pygame()

    # ------------------------------------------------------------------
    # Init & resize
    # ------------------------------------------------------------------
    def _init_pygame(self) -> None:
        pygame.init()

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

        # --- Attach Assets as a resource (images + sounds) ---
        # Base path is "assets" by default; adjust if your folder differs.
        assets = Assets(base_path=Path("assets"))

        # Try to load known sprites; skip silently if missing during dev/tests.
        for sprite_id, filename in (
            ("goldfish", "sprites/goldfish.png"),
            ("debug_fish", "debug_fish.png"),
        ):
            try:
                assets.load_image(sprite_id, filename)
            except Exception:
                # Missing assets are ok in headless/test runs.
                pass

        self.engine.resources.set("assets", assets)

    def _handle_resize(self, event: pygame.event.Event) -> None:
        """Handle VIDEORESIZE: recreate the window surface + update resources."""
        self.width, self.height = event.w, event.h

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(self.title)

        # Update renderer's surface and screen_size resource
        renderer = self.engine.resources.get("renderer")
        renderer.screen = self.screen
        self.engine.resources.set("screen_size", (self.width, self.height))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        self._running = True
        assert self.clock is not None

        while self._running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            # --- Event polling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event)

            # --- Engine update & render ---
            self.engine.update(dt)
            self.engine.render(dt)

        pygame.quit()
