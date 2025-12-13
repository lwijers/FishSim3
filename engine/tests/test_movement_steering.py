from __future__ import annotations

import pytest
from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Position, Velocity, RectSprite, MovementIntent
from engine.game.systems import MovementSystem


def test_movement_respects_accel_limit() -> None:
    world = World()
    resources = ResourceStore()
    resources.set("logical_size", (800, 600))
    resources.set("screen_size", (800, 600))
    resources.set("movement_config", {"max_accel": 10.0, "max_speed": 0.0})
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=0.0))
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=10.0, height=10.0, color=(0, 0, 0)))
    world.add_component(eid, MovementIntent(target_vx=100.0, target_vy=0.0))

    move_sys.update(world, dt=0.5)

    (_, vel) = next(world.view(Velocity))
    # Max accel 10 => max delta_v = 5 over dt=0.5
    assert vel.vx == 5.0
    assert vel.vy == 0.0


def test_intent_updates_on_bounce() -> None:
    world = World()
    resources = ResourceStore()
    resources.set("logical_size", (10.0, 10.0))
    resources.set("movement_config", {"max_accel": 0.0, "max_speed": 100.0})
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=9.0, y=5.0))
    world.add_component(eid, Velocity(vx=2.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    intent = MovementIntent(target_vx=2.0, target_vy=0.0)
    world.add_component(eid, intent)

    move_sys.update(world, dt=1.0)

    pos = world.get_components(Position)[eid]
    vel = world.get_components(Velocity)[eid]
    assert pos.x == pytest.approx(9.0)
    assert vel.vx < 0.0  # redirected inward
    assert intent.target_vx == vel.vx  # intent matches new direction


def test_avoidance_pushes_inward_near_wall() -> None:
    world = World()
    resources = ResourceStore()
    resources.set(
        "movement_config",
        {
            "max_accel": 0.0,
            "max_speed": 0.0,
            "avoidance": {"margin": 10.0, "strength": 100.0},
        },
    )
    resources.set("logical_size", (100.0, 100.0))
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=90.0, y=50.0))  # at right edge (max_x = 90)
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=10.0, height=10.0, color=(0, 0, 0)))
    world.add_component(eid, MovementIntent(target_vx=0.0, target_vy=0.0))

    move_sys.update(world, dt=0.5)

    pos = world.get_components(Position)[eid]
    vel = world.get_components(Velocity)[eid]
    assert pos.x < 90.0  # nudged inward
    assert vel.vx < 0.0  # velocity directed inward


def test_pellet_without_intent_still_bounces() -> None:
    world = World()
    resources = ResourceStore()
    resources.set("logical_size", (20.0, 20.0))
    resources.set("movement_config", {"max_accel": 0.0, "max_speed": 0.0})
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=18.0, y=10.0))
    world.add_component(eid, Velocity(vx=5.0, vy=0.0))
    world.add_component(eid, RectSprite(width=2.0, height=2.0, color=(0, 0, 0)))
    # No MovementIntent -> legacy bounce path

    move_sys.update(world, dt=1.0)

    pos = world.get_components(Position)[eid]
    vel = world.get_components(Velocity)[eid]
    assert pos.x == pytest.approx(18.0)
    assert vel.vx < 0.0  # bounced back


def test_redirect_uses_min_speed_when_stopped() -> None:
    world = World()
    resources = ResourceStore()
    resources.set(
        "movement_config",
        {
            "max_accel": 0.0,
            "max_speed": 10.0,
            "redirect": {"min_speed": 25.0, "tangent_jitter": 0.0},
        },
    )
    resources.set("logical_size", (10.0, 10.0))
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=9.5, y=5.0))  # slightly outside max_x=9 -> triggers redirect
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    intent = MovementIntent(target_vx=0.0, target_vy=0.0)
    world.add_component(eid, intent)

    move_sys.update(world, dt=0.5)

    vel = world.get_components(Velocity)[eid]
    speed = (vel.vx * vel.vx + vel.vy * vel.vy) ** 0.5
    assert speed >= 25.0  # picked up min_speed on redirect
    assert intent.target_vx == vel.vx
    assert intent.target_vy == vel.vy


def test_avoid_brake_min_factor_is_clamped() -> None:
    world = World()
    resources = ResourceStore()
    # brake_min_factor > 1 should clamp to 1 (no speed-up)
    resources.set(
        "movement_config",
        {
            "max_accel": 0.0,
            "max_speed": 0.0,
            "avoidance": {"margin": 2.0, "brake_min_factor": 2.0},
        },
    )
    resources.set("logical_size", (20.0, 20.0))
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=0.5, y=10.0))  # inside margin to left wall
    world.add_component(eid, Velocity(vx=5.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    world.add_component(eid, MovementIntent(target_vx=5.0, target_vy=0.0))

    move_sys.update(world, dt=0.5)

    vel = world.get_components(Velocity)[eid]
    speed = (vel.vx * vel.vx + vel.vy * vel.vy) ** 0.5
    # With clamp, speed should not increase beyond the original 5.0
    assert speed <= 5.0


def test_avoid_push_respects_max_accel() -> None:
    world = World()
    resources = ResourceStore()
    resources.set(
        "movement_config",
        {
            "max_accel": 5.0,  # cap push magnitude
            "max_speed": 0.0,
            "avoidance": {"margin": 10.0, "strength": 1000.0},
        },
    )
    resources.set("logical_size", (100.0, 100.0))
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=1.0, y=50.0))  # deep in margin near left wall
    world.add_component(eid, Velocity(vx=0.0, vy=0.0))
    world.add_component(eid, RectSprite(width=2.0, height=2.0, color=(0, 0, 0)))
    world.add_component(eid, MovementIntent(target_vx=0.0, target_vy=0.0))

    move_sys.update(world, dt=1.0)

    vel = world.get_components(Velocity)[eid]
    speed = (vel.vx * vel.vx + vel.vy * vel.vy) ** 0.5
    # delta_v magnitude should be capped by max_accel * dt
    assert speed <= 5.0 + 1e-6


def test_max_speed_clamps_before_integration() -> None:
    world = World()
    resources = ResourceStore()
    resources.set(
        "movement_config",
        {
            "max_accel": 0.0,
            "max_speed": 1.0,
        },
    )
    resources.set("logical_size", (100.0, 100.0))
    move_sys = MovementSystem(resources)

    eid = world.create_entity()
    world.add_component(eid, Position(x=0.0, y=0.0))
    world.add_component(eid, Velocity(vx=10.0, vy=0.0))
    world.add_component(eid, RectSprite(width=1.0, height=1.0, color=(0, 0, 0)))
    world.add_component(eid, MovementIntent(target_vx=10.0, target_vy=0.0))

    move_sys.update(world, dt=1.0)

    pos = world.get_components(Position)[eid]
    vel = world.get_components(Velocity)[eid]
    assert pos.x == pytest.approx(1.0)  # max_speed * dt
    assert vel.vx == pytest.approx(1.0)
