# engine/game/components/fish.py
from dataclasses import dataclass


@dataclass
class Fish:
    """
    Domain component tagging an entity as a fish and
    tying it to a species definition.
    """
    species_id: str
