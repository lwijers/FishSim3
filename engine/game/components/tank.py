# engine/game/components/tank.py
from dataclasses import dataclass

@dataclass
class Tank:
    """
    Logical tank properties (identity + rules).
    """
    tank_id: str
    max_fish: int
