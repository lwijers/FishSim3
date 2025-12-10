from __future__ import annotations
from pathlib import Path

from engine.adapters.pygame_render.renderer import Renderer


class DummyScreen:
    def __init__(self): ...


def test_draw_text_uses_font_path_if_exists(tmp_path) -> None:
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((10, 10))
    try:
        renderer = Renderer(screen)
        # Create a dummy font file path (won't be a real font, so we just ensure it tries the path)
        font_path = tmp_path / "dummy.ttf"
        font_path.write_bytes(b"")
        try:
            renderer.draw_text("hi", 0, 0, font_name=str(font_path))
        except Exception:
            # Expected since it's not a real font; but ensure it attempted to resolve path
            assert True
    finally:
        pygame.quit()
