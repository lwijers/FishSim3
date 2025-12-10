# engine/app/boot.py
from __future__ import annotations
from dataclasses import dataclass
import random

from engine.ecs import World
from engine.scheduling import Scheduler
from engine.resources import ResourceStore
from engine.events import EventBus
from engine.game.systems import MovementSystem, RectRenderSystem, FishFSMSystem
from engine.game.factories import (
    load_species_config,
    create_fish,      # still exported; handy later
    create_tank,
    load_tank_config,
)
from engine.game.components import Position, RectSprite, UIHitbox, UIButton, SpriteRef, UIElement, UILabel, UIPanel
from engine.game.rules import spawn_fish_in_tank_if_allowed
from engine.game.components.tank_bounds import TankBounds
from engine.game.data.configs import load_settings_config, load_ui_config, load_pellet_config, load_falling_config, load_fsm_config
from engine.app.constants import (
    RNG_ROOT_SEED,
    RNG_MAX_INT,
    DEFAULT_TANK_ID,
    DEFAULT_WINDOW_SIZE,
)
from engine.game.systems import (
    MovementSystem,
    RectRenderSystem,
    FishFSMSystem,
    SpriteRenderSystem,
    PlacementSystem,
    FallingSystem,
    UIButtonSystem,
    KeyboardSystem,
    MouseSystem,
    UILabelSystem,
    DebugMenuSystem,
    FishStateLabelSystem,
)


def _validate_ui_config(ui_cfg: dict) -> None:
    styles = ui_cfg.get("styles", {})
    comps = ui_cfg.get("components", [])
    for comp in comps:
        if "type" not in comp:
            raise ValueError("UI component missing 'type'")
        style_key = comp.get("style")
        if style_key is not None and style_key not in styles:
            raise ValueError(f"UI component {comp.get('id', comp['type'])!r} references unknown style {style_key!r}")
        ctype = comp["type"]
        if ctype not in ("label",) and ("width" not in comp or "height" not in comp):
            raise ValueError(f"UI component {comp.get('id', comp['type'])!r} must define width/height")

@dataclass
class Engine:
    """
    Simple facade wrapping world + scheduler + resources.
    PygameApp will call engine.update(...) and engine.render(...).
    """
    world: World
    scheduler: Scheduler
    resources: ResourceStore

    def update(self, dt: float) -> None:
        self.scheduler.update(self.world, dt)

    def render(self, dt: float) -> None:
        self.scheduler.render(self.world, dt)


def _populate_debug_fish(
    world: World,
    species_cfg,
    tank_eid,
    tank_def,
    rng: random.Random,
) -> None:
    """
    Spawn a few test fish based on species.json so we can see something on screen.
    All fish are assigned to the given tank entity and respect its max_fish.

    Magic numbers (count, margin) now come from tank data, with small defaults:
    - tank_def["debug_spawn"]["count"]   (fallback 8)
    - tank_def["debug_spawn"]["margin"]  (fallback 50.0)
    """
    debug_cfg = tank_def.get("debug_spawn", {})
    count = int(debug_cfg.get("count", 8))
    margin = max(0.0, float(debug_cfg.get("margin", 50.0)))

    # Get the tank's screen rect from its TankBounds component
    bounds_store = world.get_components(TankBounds)
    bounds = bounds_store.get(tank_eid)
    if bounds is not None:
        left = float(bounds.x)
        top = float(bounds.y)
        right = float(bounds.x + bounds.width)
        bottom = float(bounds.y + bounds.height)
        width = right - left
        height = bottom - top
    else:
        # Fallback if something went wrong; shouldn't normally happen.
        default_w, default_h = DEFAULT_WINDOW_SIZE
        left, top = 0.0, 0.0
        right, bottom = float(default_w), float(default_h)
        width = right - left
        height = bottom - top

    # Ensure the spawn area is valid even if a config margin is too large.
    if width <= 0.0 or height <= 0.0:
        return
    max_margin = max(0.0, min(width, height) / 2.0 - 1.0)
    margin = min(margin, max_margin)

    # Spawn within the tank rect, keeping a configurable margin from edges.
    for _ in range(count):
        x = rng.uniform(left + margin, right - margin)
        y = rng.uniform(top + margin, bottom - margin)
        spawn_fish_in_tank_if_allowed(
            world,
            tank_eid=tank_eid,
            species_cfg=species_cfg,
            species_id="debug_fish",
            x=x,
            y=y,
            rng=rng,
        )


def _create_ui_from_config(world: World, resources: ResourceStore, logical_w: float, logical_h: float) -> None:
    ui_cfg = resources.try_get("ui_config", {})
    components = ui_cfg.get("components", [])
    styles = ui_cfg.get("styles", {})

    for comp in components:
        ctype = comp.get("type")
        style_key = comp.get("style")
        if ctype == "button":
            width = float(comp.get("width", 64.0))
            height = float(comp.get("height", 64.0))
            x = float(comp.get("x", 0.0))
            y_val = comp.get("y")
            bottom = comp.get("bottom")
            if y_val is None:
                bottom_val = float(bottom if bottom is not None else 0.0)
                y = max(0.0, logical_h - height - bottom_val)
            else:
                y = float(y_val)
            tool_id = comp.get("tool")
            exclusive_group = comp.get("exclusive_group")
            deactivate_on_right_click = bool(comp.get("deactivate_on_right_click", True))
            icon_cfg = comp.get("icon", {})
            icon_size = float(icon_cfg.get("size", 32.0))
            icon_sprite = icon_cfg.get("sprite_id")

            btn_eid = world.create_entity()
            world.add_component(btn_eid, Position(x=x, y=y))
            color = tuple(styles.get(style_key, {}).get("inactive", (42, 82, 110)))
            world.add_component(btn_eid, RectSprite(width=width, height=height, color=color))
            world.add_component(btn_eid, UIHitbox(width=width, height=height))
            world.add_component(btn_eid, UIElement(width=width, height=height, style=style_key, element_id=comp.get("id"), visible_flag=comp.get("visible_flag")))
            world.add_component(btn_eid, UIButton(tool_id=tool_id, active=False, exclusive_group=exclusive_group, deactivate_on_right_click=deactivate_on_right_click))

            if icon_sprite:
                icon_x = x + (width - icon_size) / 2.0
                icon_y = y + (height - icon_size) / 2.0
                icon_eid = world.create_entity()
                world.add_component(icon_eid, Position(x=icon_x, y=icon_y))
                world.add_component(icon_eid, SpriteRef(sprite_id=icon_sprite, width=icon_size, height=icon_size))
                world.add_component(icon_eid, UIElement(width=icon_size, height=icon_size, style=None, element_id=f"{comp.get('id')}_icon", visible_flag=comp.get("visible_flag")))

        elif ctype == "panel":
            width = float(comp.get("width", 0.0))
            height = float(comp.get("height", 0.0))
            x = float(comp.get("x", 0.0))
            y_val = comp.get("y")
            bottom = comp.get("bottom")
            if y_val is None:
                bottom_val = float(bottom if bottom is not None else 0.0)
                y = max(0.0, logical_h - height - bottom_val)
            else:
                y = float(y_val)
            color = tuple(styles.get(style_key, {}).get("inactive", (0, 0, 0, 180)))
            eid = world.create_entity()
            world.add_component(eid, Position(x=x, y=y))
            world.add_component(eid, RectSprite(width=width, height=height, color=color))
            world.add_component(eid, UIElement(width=width, height=height, style=style_key, element_id=comp.get("id"), visible_flag=comp.get("visible_flag")))
            world.add_component(eid, UIHitbox(width=width, height=height))
            world.add_component(eid, UIPanel(panel_id=comp.get("id"), visible_flag=comp.get("visible_flag")))
            panel_visibility = resources.try_get("panel_visibility", {})
            panel_visibility[comp.get("id")] = bool(resources.try_get(comp.get("visible_flag"), False)) if comp.get("visible_flag") else False
            resources.set("panel_visibility", panel_visibility)

        elif ctype == "label":
            x = float(comp.get("x", 0.0))
            y_val = comp.get("y", 0.0)
            y = float(y_val)
            text_key = comp.get("text_key", "")
            eid = world.create_entity()
            world.add_component(eid, Position(x=x, y=y))
            world.add_component(eid, UILabel(text=text_key, text_key=text_key))
            width = float(comp.get("width", 0.0))
            height = float(comp.get("height", 0.0))
            world.add_component(
                eid,
                UIElement(
                    width=width,
                    height=height,
                    style=style_key,
                    element_id=comp.get("id"),
                    visible_flag=comp.get("visible_flag"),
                ),
            )
            panel_parent = comp.get("panel")
            if panel_parent:
                # Link this element to parent panel for visibility inheritance
                links = resources.try_get("ui_panel_links", {})
                links[eid] = panel_parent
                resources.set("ui_panel_links", links)

    # Store styles for renderers/systems
    resources.set("ui_styles", styles)
def build_engine() -> Engine:
    """
    Composition root for the core engine.
    - Creates ResourceStore + EventBus.
    - Creates deterministic RNGs.
    - Loads settings, UI, species + tank config from data files.
    - Creates World + Scheduler and registers systems.
    - Spawns a few bouncing fish rectangles per config.
    """
    resources = ResourceStore()

    # ------------------------------------------------------------------
    # User-tweakable configs
    # ------------------------------------------------------------------
    settings = load_settings_config()
    ui_cfg = load_ui_config()
    resources.set("settings", settings)
    resources.set("ui_config", ui_cfg)
    resources.set("ui_styles", ui_cfg.get("styles", {}))

    # Expose logical_size if configured; RectRenderSystem can fall back
    logical_cfg = settings.get("logical_size", {})
    logical_w = float(logical_cfg.get("width", 0.0))
    logical_h = float(logical_cfg.get("height", 0.0))
    if logical_w > 0.0 and logical_h > 0.0:
        resources.set("logical_size", (logical_w, logical_h))
    else:
        logical_w, logical_h = DEFAULT_WINDOW_SIZE

    # Global event bus resource (will be used later by game & adapters)
    events = EventBus()
    resources.register("events", events)
    resources.set("active_tool", None)

    # ------------------------------------------------------------------
    # Deterministic RNG hierarchy
    # ------------------------------------------------------------------
    rng_root = random.Random(RNG_ROOT_SEED)
    resources.set("rng_root", rng_root)
    resources.set("rng_ai", random.Random(rng_root.randint(0, RNG_MAX_INT)))
    resources.set("rng_spawns", random.Random(rng_root.randint(0, RNG_MAX_INT)))

    # ------------------------------------------------------------------
    # Load game object configs
    # ------------------------------------------------------------------
    species_cfg = load_species_config()
    resources.set("species_config", species_cfg)

    tank_cfg = load_tank_config()
    resources.set("tank_config", tank_cfg)

    pellet_cfg = load_pellet_config()
    resources.set("pellet_config", pellet_cfg)

    falling_cfg = load_falling_config()
    resources.set("falling_config", falling_cfg)
    fsm_cfg = load_fsm_config()
    resources.set("fsm_config", fsm_cfg)
    # Validate UI config components reference defined styles
    _validate_ui_config(ui_cfg)

    # ------------------------------------------------------------------
    # World + scheduler + systems
    # ------------------------------------------------------------------
    world = World()
    scheduler = Scheduler()

    fsm_sys = FishFSMSystem(resources)
    ui_button_sys = UIButtonSystem(resources)
    keyboard_sys = KeyboardSystem(resources)
    mouse_sys = MouseSystem(resources)
    debug_menu_sys = DebugMenuSystem(resources)
    placement_sys = PlacementSystem(resources)
    falling_sys = FallingSystem(resources)
    move_sys = MovementSystem(resources)
    rect_render_sys = RectRenderSystem(resources)
    sprite_render_sys = SpriteRenderSystem(resources)
    fish_state_label_sys = FishStateLabelSystem(resources)

    # Order matters:
    # - FSM before Movement in logic
    # - UI buttons process clicks before placement
    # - Keyboard/mouse state update before other logic
    # - Placement consumes input events and queues commands before movement
    # - Falling applies gravity before integration/movement
    # - RectRenderSystem clears & presents
    # - SpriteRenderSystem draws on top (no clear/present)
    scheduler.add_system(fsm_sys, phase="logic")
    scheduler.add_system(keyboard_sys, phase="logic")
    scheduler.add_system(mouse_sys, phase="logic")
    scheduler.add_system(ui_button_sys, phase="logic")
    scheduler.add_system(debug_menu_sys, phase="logic")
    scheduler.add_system(placement_sys, phase="logic")
    scheduler.add_system(falling_sys, phase="logic")
    scheduler.add_system(move_sys, phase="logic")
    scheduler.add_system(rect_render_sys, phase="render")
    scheduler.add_system(UILabelSystem(resources), phase="render")
    scheduler.add_system(fish_state_label_sys, phase="render")
    scheduler.add_system(sprite_render_sys, phase="render")

    # ------------------------------------------------------------------
    # Create initial tank
    # ------------------------------------------------------------------
    tanks_map = tank_cfg.get("tanks") or {}
    if not tanks_map:
        raise ValueError("tanks.json must define at least one tank in 'tanks'.")

    starting_tank_id = tank_cfg.get("starting_tank_id", DEFAULT_TANK_ID)
    tank_def = tanks_map.get(starting_tank_id)
    if tank_def is None:
        # Fallback to DEFAULT_TANK_ID if present, otherwise the first entry.
        fallback_id = DEFAULT_TANK_ID if DEFAULT_TANK_ID in tanks_map else next(iter(tanks_map))
        starting_tank_id = fallback_id
        tank_def = tanks_map[starting_tank_id]

    bounds = tank_def.get("bounds")
    if not (isinstance(bounds, (list, tuple)) and len(bounds) == 4):
        raise ValueError(f"Tank {starting_tank_id!r} is missing a 4-element 'bounds' list.")
    x, y, width, height = (
        float(bounds[0]),
        float(bounds[1]),
        float(bounds[2]),
        float(bounds[3]),
    )
    max_fish = int(tank_def.get("max_fish", 0))
    if max_fish <= 0:
        raise ValueError(f"Tank {starting_tank_id!r} must define max_fish > 0.")

    tank_eid = create_tank(
        world,
        tank_id=starting_tank_id,
        max_fish=max_fish,
        x=x,
        y=y,
        width=width,
        height=height,
    )

    # ------------------------------------------------------------------
    # Debug entities so we see something
    # ------------------------------------------------------------------
    rng_spawns: random.Random = resources.get("rng_spawns")
    _populate_debug_fish(world, species_cfg, tank_eid, tank_def, rng_spawns)

    # ------------------------------------------------------------------
    # UI from config
    # ------------------------------------------------------------------
    _create_ui_from_config(world, resources, logical_w, logical_h)

    return Engine(world=world, scheduler=scheduler, resources=resources)
