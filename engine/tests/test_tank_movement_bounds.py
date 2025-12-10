# engine/tests/test_tank_movement_bounds.py
from __future__ import annotations
from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import (
    Position,
    Velocity,
    RectSprite,
    Tank,
    TankBounds,
    InTank,
)
from engine.game.systems import MovementSystem



def _make_world_with_movement(screen_size=(800, 600)):
    world = World()
    resources = ResourceStore()
    resources.set("logical_size", screen_size)
    resources.set("screen_size", screen_size)
    move_sys = MovementSystem(resources)
    return world, resources, move_sys


def test_fish_in_tank_bounces_against_tank_bounds_not_screen() -> None:
    """
    TankBounds should restrict movement:
    - We create a tank smaller than the screen, put a fish near the right edge,
      and move it right.
    - It should bounce at the tank's right edge, even though the screen is bigger.
    """
    world, resources, move_sys = _make_world_with_movement(screen_size=(800, 600))

    # Define a small tank in the middle of the screen
    tank_eid = world.create_entity()
    world.add_component(tank_eid, Tank(tank_id="small_tank", max_fish=10))
    world.add_component(tank_eid, TankBounds(x=100.0, y=50.0, width=200.0, height=200.0))

    # Tank bounds => rect [100, 50] to [300, 250]
    # We'll put the fish near the right edge inside the tank.
    sprite = RectSprite(width=10.0, height=10.0, color=(255, 255, 255))

    # For the top-left of the sprite:
    #   min_x = 100
    #   max_x = 300 - 10 = 290
    start_x = 289.0  # 1 pixel left of max_x
    pos = Position(x=start_x, y=100.0)
    vel = Velocity(vx=50.0, vy=0.0)

    fish_eid = world.create_entity()
    world.add_component(fish_eid, pos)
    world.add_component(fish_eid, vel)
    world.add_component(fish_eid, sprite)
    world.add_component(fish_eid, InTank(tank=tank_eid))

    # dt=1.0 -> naive integration would put x at 339.0,
    # which is beyond the tank's right edge and also still within the screen.
    move_sys.update(world, dt=1.0)

    # After the update, we expect:
    # - x clamped to max_x (= 290)
    # - vx redirected inward (negative)
    assert pos.x == 290.0
    assert vel.vx < 0.0


def test_fish_without_tank_uses_full_screen_bounds() -> None:
    """
    As a fallback, entities without InTank (or whose tank has no TankBounds)
    should still use full-screen bounds.
    This guards the 'fallback to screen' code path.
    """
    screen_w, screen_h = 400, 300
    world, resources, move_sys = _make_world_with_movement(screen_size=(screen_w, screen_h))

    sprite = RectSprite(width=20.0, height=20.0, color=(0, 255, 0))

    # Place near the right edge of the *screen* and move right.
    start_x = screen_w - sprite.width - 5.0  # 400 - 20 - 5 = 375
    pos = Position(x=start_x, y=100.0)
    vel = Velocity(vx=100.0, vy=0.0)

    eid = world.create_entity()
    world.add_component(eid, pos)
    world.add_component(eid, vel)
    world.add_component(eid, sprite)
    # Crucially: NO InTank component here.

    move_sys.update(world, dt=0.2)  # we cross the right edge

    # Clamped to 380 and velocity redirected inward
    assert pos.x == screen_w - sprite.width
    assert vel.vx < 0.0
