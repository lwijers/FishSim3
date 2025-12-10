from __future__ import annotations
from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Position, Velocity, RectSprite
from engine.game.systems import MovementSystem


def make_world_and_system(screen_size=(800, 600)):
    """Helper: world with one movement system + resources."""
    world = World()
    resources = ResourceStore()
    # In the new model, logical space drives movement.
    resources.set("logical_size", screen_size)
    # screen_size is still useful for rendering, so we keep it too.
    resources.set("screen_size", screen_size)
    move_sys = MovementSystem(resources)
    return world, resources, move_sys


def test_movement_integrates_position() -> None:
    """
    Given an entity with Position + Velocity + RectSprite,
    MovementSystem should integrate position as pos += v * dt
    and then apply boundary checks (clamp inside bounds).
    """
    world, resources, move_sys = make_world_and_system(screen_size=(800, 600))

    eid = world.create_entity()
    pos = Position(x=10.0, y=20.0)
    vel = Velocity(vx=100.0, vy=-50.0)
    sprite = RectSprite(width=50.0, height=30.0, color=(255, 0, 0))

    world.add_component(eid, pos)
    world.add_component(eid, vel)
    world.add_component(eid, sprite)

    # Run one update with dt = 0.5 seconds
    move_sys.update(world, dt=0.5)

    # Fetch components directly from the stores
    pos_store = world.get_components(Position)
    vel_store = world.get_components(Velocity)

    # There should be exactly one entity
    assert len(pos_store) == 1
    assert len(vel_store) == 1

    (only_eid, new_pos) = next(iter(pos_store.items()))
    new_vel = vel_store[only_eid]

    assert only_eid == eid

    # X: integrated only (no horizontal bounce in this setup)
    # 10 + 100 * 0.5 = 60
    assert new_pos.x == 60.0

    # Y: would be 20 + (-50 * 0.5) = -5,
    # but we hit the top border, so it gets clamped to 0 and redirected upward
    assert new_pos.y == 0.0
    assert new_vel.vy >= 0.0

    # vx should be unchanged
    assert new_vel.vx == 100.0

def test_movement_bounces_on_right_edge() -> None:
    """
    If a rectangle moves beyond the right edge, it should be clamped inside
    and its vx should be zeroed (no bounce).
    """
    screen_w, screen_h = 400, 300
    world, resources, move_sys = make_world_and_system(screen_size=(screen_w, screen_h))

    eid = world.create_entity()
    sprite = RectSprite(width=50.0, height=30.0, color=(0, 255, 0))

    # Start close to the right edge, moving right
    pos = Position(x=screen_w - sprite.width - 5.0, y=100.0)
    vel = Velocity(vx=100.0, vy=0.0)

    world.add_component(eid, pos)
    world.add_component(eid, vel)
    world.add_component(eid, sprite)

    # dt big enough to cross the boundary
    move_sys.update(world, dt=0.2)

    pos_store = world.get_components(Position)
    vel_store = world.get_components(Velocity)

    assert len(pos_store) == 1
    assert len(vel_store) == 1

    (only_eid, new_pos) = next(iter(pos_store.items()))
    new_vel = vel_store[only_eid]

    assert only_eid == eid

    # X should be clamped to screen_w - width
    assert new_pos.x == screen_w - sprite.width
    # Velocity should head back inside
    assert new_vel.vx < 0.0
