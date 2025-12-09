# engine/game/data/jsonio.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Directory containing all game data files (JSON, etc.)
DATA_DIR = Path(__file__).resolve().parent


def data_path(filename: str) -> Path:
    """
    Return the full path to a data file in this directory.

    Example:
        data_path("species.json") -> .../engine/game/data/species.json
    """
    return DATA_DIR / filename


def load_json(filename: str) -> Any:
    """
    Load a JSON file from the data directory and return the parsed object.
    """
    path = data_path(filename)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
