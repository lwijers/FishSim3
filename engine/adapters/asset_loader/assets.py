# engine/adapters/asset_loader/assets.py
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pygame


class Assets:
    """Simple asset store for images and sounds.

    Lives in the adapters layer and is responsible for loading assets from disk
    using pygame. Game systems should only see this via the ResourceStore,
    not import pygame directly.
    """

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)
        self._images: Dict[str, pygame.Surface] = {}
        self._sounds: Dict[str, pygame.mixer.Sound] = {}

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------
    def load_image(self, sprite_id: str, filename: str) -> None:
        """Load an image file and store it under the given sprite_id."""
        path = self._base_path / filename
        image = pygame.image.load(str(path)).convert_alpha()
        self._images[sprite_id] = image

    def has_image(self, sprite_id: str) -> bool:
        return sprite_id in self._images

    def get_image(self, sprite_id: str) -> pygame.Surface:
        return self._images[sprite_id]

    # ------------------------------------------------------------------
    # Sounds (for later)
    # ------------------------------------------------------------------
    def load_sound(self, sound_id: str, filename: str) -> None:
        """Load a sound file and store it under the given sound_id.

        Requires pygame.mixer to be initialised before calling.
        """
        path = self._base_path / filename
        sound = pygame.mixer.Sound(str(path))
        self._sounds[sound_id] = sound

    def has_sound(self, sound_id: str) -> bool:
        return sound_id in self._sounds

    def get_sound(self, sound_id: str) -> pygame.mixer.Sound:
        return self._sounds[sound_id]
