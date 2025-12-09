# engine/app/main.py
from __future__ import annotations

from engine.app.boot import build_engine
from engine.adapters.pygame_render.app import PygameApp
from engine.game.data.configs import load_settings_config
from engine.app.constants import DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_TITLE


def main() -> None:
    engine = build_engine()

    # Window settings are user-tweakable in settings.json
    settings = load_settings_config()
    window_cfg = settings.get("window", {})

    default_w, default_h = DEFAULT_WINDOW_SIZE
    width = int(window_cfg.get("width", default_w))
    height = int(window_cfg.get("height", default_h))
    title = window_cfg.get("title", DEFAULT_WINDOW_TITLE)

    app = PygameApp(engine, width=width, height=height, title=title)
    app.run()


if __name__ == "__main__":
    main()
