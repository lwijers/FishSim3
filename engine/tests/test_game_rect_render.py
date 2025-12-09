# engine/tests/test_game_rect_render.py
from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Position, RectSprite
from engine.game.systems import RectRenderSystem


class FakeRenderer:
    """
    Test double for the Renderer:
    - records calls to clear(), draw_rect(), present()
    - no pygame dependency
    """
    def __init__(self) -> None:
        self.cleared = False
        self.presented = False
        self.draw_calls = []  # list of (x, y, w, h, color, outline_width)

    def clear(self) -> None:
        self.cleared = True

    def present(self) -> None:
        self.presented = True

    def draw_rect(self, x, y, w, h, color, outline_width=0) -> None:
        self.draw_calls.append((x, y, w, h, color, outline_width))


def _make_world_and_render_system(
    logical_size=(800, 600),
    screen_size=(800, 600),
):
    """
    Helper: create World + ResourceStore + RectRenderSystem + FakeRenderer
    with given logical and screen sizes.
    """
    world = World()
    resources = ResourceStore()
    fake_renderer = FakeRenderer()

    resources.set("renderer", fake_renderer)
    resources.set("logical_size", logical_size)
    resources.set("screen_size", screen_size)

    render_sys = RectRenderSystem(resources)
    return world, resources, render_sys, fake_renderer


def test_rect_render_system_draws_rectangles_no_scaling() -> None:
    """
    When logical_size == screen_size, RectRenderSystem should:
      - clear the renderer
      - draw one rect per entity with Position + RectSprite
      - present the frame
      - pass coordinates through 1:1 (no scaling)
    """
    logical_size = (800, 600)
    screen_size = (800, 600)
    world, resources, render_sys, fake_renderer = _make_world_and_render_system(
        logical_size=logical_size,
        screen_size=screen_size,
    )

    # Create two entities with Position + RectSprite in logical space
    eid1 = world.create_entity()
    world.add_component(eid1, Position(x=10.0, y=20.0))
    world.add_component(
        eid1,
        RectSprite(width=30.0, height=40.0, color=(255, 0, 0)),
    )

    eid2 = world.create_entity()
    world.add_component(eid2, Position(x=100.0, y=50.0))
    world.add_component(
        eid2,
        RectSprite(width=60.0, height=20.0, color=(0, 255, 0)),
    )

    # Run render system once
    render_sys.update(world, dt=0.016)

    # Assert renderer was used as expected
    assert fake_renderer.cleared is True
    assert fake_renderer.presented is True
    assert len(fake_renderer.draw_calls) == 2

    calls = fake_renderer.draw_calls

    # Because scale_x == scale_y == 1, we expect coordinates unchanged
    assert any(
        c[0] == 10.0 and c[1] == 20.0 and c[2] == 30.0 and c[3] == 40.0 and c[4] == (255, 0, 0)
        for c in calls
    )
    assert any(
        c[0] == 100.0 and c[1] == 50.0 and c[2] == 60.0 and c[3] == 20.0 and c[4] == (0, 255, 0)
        for c in calls
    )


def test_rect_render_system_scales_logical_to_screen() -> None:
    """
    When screen_size != logical_size, RectRenderSystem should scale logical
    positions and sizes into screen space.

    Example:
      logical_size = (400, 300)
      screen_size  = (800, 600)
      => scale_x = scale_y = 2.0
    """
    logical_size = (400, 300)
    screen_size = (800, 600)
    world, resources, render_sys, fake_renderer = _make_world_and_render_system(
        logical_size=logical_size,
        screen_size=screen_size,
    )

    # One entity in logical space
    eid = world.create_entity()
    world.add_component(eid, Position(x=10.0, y=20.0))  # logical coords
    world.add_component(
        eid,
        RectSprite(width=30.0, height=40.0, color=(123, 111, 222)),
    )

    # With logical (400x300) → screen (800x600), scale = 2.0 both axes:
    #   x_px = 10 * 2 = 20
    #   y_px = 20 * 2 = 40
    #   w_px = 30 * 2 = 60
    #   h_px = 40 * 2 = 80
    render_sys.update(world, dt=0.016)

    assert fake_renderer.cleared is True
    assert fake_renderer.presented is True
    assert len(fake_renderer.draw_calls) == 1

    (x_px, y_px, w_px, h_px, color, outline_width) = fake_renderer.draw_calls[0]
    assert x_px == 20.0
    assert y_px == 40.0
    assert w_px == 60.0
    assert h_px == 80.0
    assert color == (123, 111, 222)
    assert outline_width == 0
