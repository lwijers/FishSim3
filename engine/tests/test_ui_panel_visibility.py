from __future__ import annotations

from engine.ecs import World
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.components import Position, RectSprite, UIElement, UIPanel, UILabel
from engine.game.systems import RectRenderSystem, UILabelSystem


class FakeRenderer:
    def __init__(self) -> None:
        self.draw_rect_calls = []
        self.text_calls = []

    def clear(self): ...
    def present(self): ...

    def draw_rect(self, *args, **kwargs):
        self.draw_rect_calls.append(args)

    def draw_text(self, text, x, y, color=(255, 255, 255), font_size=16, font_name=None):
        self.text_calls.append((text, x, y, color, font_size, font_name))


def test_panel_visibility_hides_children() -> None:
    resources = ResourceStore()
    bus = EventBus()
    resources.register("events", bus)
    resources.set("ui_styles", {})
    resources.set("screen_size", (800, 600))
    resources.set("logical_size", (800, 600))
    resources.set("panel_visibility", {})
    resources.set("ui_panel_links", {})
    panel_visibility = resources.get("panel_visibility")
    panel_visibility["panel1"] = False

    renderer = FakeRenderer()
    resources.set("renderer", renderer)

    world = World()
    # panel
    panel_eid = world.create_entity()
    world.add_component(panel_eid, Position(x=0.0, y=0.0))
    world.add_component(panel_eid, RectSprite(width=100.0, height=50.0, color=(1, 1, 1)))
    world.add_component(panel_eid, UIElement(width=100.0, height=50.0, style=None, element_id="panel1", visible_flag="panel_visible_flag"))
    world.add_component(panel_eid, UIPanel(panel_id="panel1", visible_flag="panel_visible_flag"))
    resources.set("panel_visibility", {"panel1": False})
    resources.get("ui_panel_links")[panel_eid] = None

    # child label linked to panel
    label_eid = world.create_entity()
    world.add_component(label_eid, Position(x=10.0, y=10.0))
    world.add_component(label_eid, UILabel(text="hello", text_key="hello"))
    world.add_component(label_eid, UIElement(width=0.0, height=0.0, style=None, element_id="lbl1", visible_flag=None))
    resources.get("ui_panel_links")[label_eid] = "panel1"

    rect_sys = RectRenderSystem(resources)
    label_sys = UILabelSystem(resources)

    rect_sys.update(world, dt=0.016)
    label_sys.update(world, dt=0.016)

    # panel hidden -> no draws
    assert renderer.draw_rect_calls == []
    assert renderer.text_calls == []

    # show panel
    panel_visibility["panel1"] = True
    resources.set("panel_visibility", panel_visibility)
    resources.set("panel_visible_flag", True)
    rect_sys.update(world, dt=0.016)
    label_sys.update(world, dt=0.016)

    assert renderer.draw_rect_calls != []
    assert renderer.text_calls != []
