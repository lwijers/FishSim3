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
from engine.game.rules import spawn_fish_in_tank_if_allowed
from engine.game.components.tank_bounds import TankBounds
from engine.game.data.configs import load_settings_config, load_ui_config
from engine.app.constants import (
    RNG_ROOT_SEED,
    RNG_MAX_INT,
    DEFAULT_TANK_ID,
    DEFAULT_WINDOW_SIZE,
)

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
    margin = float(debug_cfg.get("margin", 50.0))

    # Get the tank's screen rect from its TankBounds component
    bounds_store = world.get_components(TankBounds)
    bounds = bounds_store.get(tank_eid)
    if bounds is not None:
        left = float(bounds.x)
        top = float(bounds.y)
        right = float(bounds.x + bounds.width)
        bottom = float(bounds.y + bounds.height)
    else:
        # Fallback if something went wrong; shouldn't normally happen.
        default_w, default_h = DEFAULT_WINDOW_SIZE
        left, top = 0.0, 0.0
        right, bottom = float(default_w), float(default_h)

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

    # Expose logical_size if configured; RectRenderSystem can fall back
    logical_cfg = settings.get("logical_size", {})
    logical_w = float(logical_cfg.get("width", 0.0))
    logical_h = float(logical_cfg.get("height", 0.0))
    if logical_w > 0.0 and logical_h > 0.0:
        resources.set("logical_size", (logical_w, logical_h))

    # Global event bus resource (will be used later by game & adapters)
    events = EventBus()
    resources.register("events", events)

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

    # ------------------------------------------------------------------
    # World + scheduler + systems
    # ------------------------------------------------------------------
    world = World()
    scheduler = Scheduler()

    fsm_sys = FishFSMSystem(resources)
    move_sys = MovementSystem(resources)
    render_sys = RectRenderSystem(resources)

    # Order matters: FSM should run before MovementSystem in the logic phase.
    scheduler.add_system(fsm_sys, phase="logic")
    scheduler.add_system(move_sys, phase="logic")
    scheduler.add_system(render_sys, phase="render")

    # ------------------------------------------------------------------
    # Create initial tank
    # ------------------------------------------------------------------
    tanks_map = tank_cfg["tanks"]
    starting_tank_id = tank_cfg.get("starting_tank_id", DEFAULT_TANK_ID)
    tank_def = tanks_map[starting_tank_id]

    bounds = tank_def["bounds"]
    x, y, width, height = (
        float(bounds[0]),
        float(bounds[1]),
        float(bounds[2]),
        float(bounds[3]),
    )
    tank_eid = create_tank(
        world,
        tank_id=starting_tank_id,
        max_fish=int(tank_def["max_fish"]),
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

    return Engine(world=world, scheduler=scheduler, resources=resources)
