# engine/tests/test_data_jsonio.py
from __future__ import annotations
from pathlib import Path

from engine.game.data.jsonio import data_path, load_json
from engine.game.factories import load_species_config
from engine.game.factories.tank_factory import load_tank_config
from engine.game.data.configs import load_settings_config, load_ui_config


def test_data_path_points_to_species_file() -> None:
    """
    data_path('species.json') should return a Path pointing to an existing file
    inside the game data folder.
    """
    p = data_path("species.json")
    assert isinstance(p, Path)
    assert p.name == "species.json"
    assert p.exists(), "species.json should exist in engine/game/data"


def test_load_json_reads_species_file() -> None:
    """
    load_json('species.json') should return a dict with '_version' and 'species' keys.
    """
    raw = load_json("species.json")
    assert isinstance(raw, dict)
    assert "_version" in raw
    assert "species" in raw
    assert isinstance(raw["species"], dict)


def test_load_species_config_returns_species_map() -> None:
    """
    load_species_config should return the 'species' dict from species.json
    and contain 'debug_fish' with basic fields.
    """
    species_cfg = load_species_config()
    assert isinstance(species_cfg, dict)
    assert "debug_fish" in species_cfg
    debug = species_cfg["debug_fish"]
    assert "width" in debug
    assert "height" in debug
    assert "color" in debug
    assert "speed_range" in debug


def test_load_tank_config_reads_tanks_json() -> None:
    """
    load_tank_config should read tanks.json and expose its structure,
    including 'tank_1' with max_fish and bounds, and a valid starting_tank_id.
    """
    cfg = load_tank_config()
    assert isinstance(cfg, dict)
    assert "_version" in cfg
    assert "tanks" in cfg
    tanks = cfg["tanks"]
    assert isinstance(tanks, dict)
    assert "tank_1" in tanks

    tank1 = tanks["tank_1"]
    assert "max_fish" in tank1
    assert "bounds" in tank1
    bounds = tank1["bounds"]
    assert isinstance(bounds, list)
    assert len(bounds) == 4

    # New: starting_tank_id should exist and refer to a defined tank
    starting_id = cfg.get("starting_tank_id")
    assert starting_id is not None
    assert starting_id in tanks


def test_settings_json_exists_and_has_window_and_logical_size() -> None:
    """
    settings.json should exist and contain 'window' and 'logical_size' sections
    with width/height ints.
    """
    raw = load_settings_config()
    assert isinstance(raw, dict)
    assert "_version" in raw

    window = raw.get("window")
    assert isinstance(window, dict)
    assert isinstance(window.get("width"), int)
    assert isinstance(window.get("height"), int)
    assert isinstance(window.get("title"), str)

    logical = raw.get("logical_size")
    assert isinstance(logical, dict)
    assert isinstance(logical.get("width"), int)
    assert isinstance(logical.get("height"), int)


def test_ui_json_contains_background_color() -> None:
    """
    ui.json should exist and define a background color in colors.background
    as an RGB triple.
    """
    raw = load_ui_config()
    assert isinstance(raw, dict)
    assert "_version" in raw

    colors = raw.get("colors")
    assert isinstance(colors, dict)

    bg = colors.get("background")
    assert isinstance(bg, list)
    assert len(bg) == 3
    assert all(isinstance(c, int) for c in bg)
