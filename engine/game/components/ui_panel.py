from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UIPanel:
    panel_id: str | None = None
    visible_flag: str | None = None
