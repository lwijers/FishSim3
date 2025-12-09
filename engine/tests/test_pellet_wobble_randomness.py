from __future__ import annotations
import random

from engine.ecs import World
from engine.resources import ResourceStore
from engine.game.components import Position, RectSprite, InTank, Falling
from engine.game.components.pellet import Pellet
from engine.game.factories.pellet_factory import create_pellet_cmd
from engine.ecs.commands import CreateEntityCmd


def test_pellet_wobble_uses_rng_range_deterministically() -> None:
    cfg = {
        "size": 10.0,
        "color": [0, 0, 0],
        "falling": {
            "wobble_amplitude_range": [1.0, 3.0],
            "wobble_frequency_range": [0.5, 1.5],
            "wobble_phase_range": [0.0, 3.14],
            "wobble_time_range": [0.0, 2.0],
        },
    }
    rng = random.Random(99)

    cmd1: CreateEntityCmd = create_pellet_cmd(0.0, 0.0, 1, pellet_cfg=cfg, rng=rng)
    cmd2: CreateEntityCmd = create_pellet_cmd(0.0, 0.0, 1, pellet_cfg=cfg, rng=rng)

    fall1: Falling = cmd1.components[Falling]
    fall2: Falling = cmd2.components[Falling]

    # Deterministic given seed, but different draws
    assert fall1.wobble_amplitude != fall2.wobble_amplitude
    assert fall1.wobble_frequency != fall2.wobble_frequency
    assert fall1.wobble_phase != fall2.wobble_phase

    # Values within configured ranges
    assert 1.0 <= fall1.wobble_amplitude <= 3.0
    assert 1.0 <= fall2.wobble_amplitude <= 3.0
    assert 0.5 <= fall1.wobble_frequency <= 1.5
    assert 0.5 <= fall2.wobble_frequency <= 1.5
    assert 0.0 <= fall1.wobble_phase <= 3.14
    assert 0.0 <= fall2.wobble_phase <= 3.14
    assert 0.0 <= fall1.wobble_time <= 2.0
    assert 0.0 <= fall2.wobble_time <= 2.0
