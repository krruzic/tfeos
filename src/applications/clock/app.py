from datetime import datetime
from pathlib import Path
from typing import Optional

from appkit.base import Application, Scene
from appkit.config import Config
from appkit.graphics_helpers import Color, Font, draw_text_centered


class ClockScene(Scene):
    def __init__(self, config, app_dir: Path):
        self.config = config
        font_path = app_dir / "resources" / "7x13.bdf"
        self.font = Font(str(font_path))

    def render(self, canvas) -> None:
        canvas.Clear()

        now = datetime.now()
        if self.config.get("show_seconds", True):
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%H:%M")

        color_hex = self.config.get("color", "#ffffff")
        color = Color.from_hex(color_hex)

        y_pos = 8 + self.font.baseline
        draw_text_centered(canvas, self.font, y_pos, color, time_str)

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            return "menu"
        return None


class App(Application):
    def on_config_changed(self, new_config: Config):
        return

    def get_framerate(self) -> int:
        return 1

    def default_scene(self) -> Scene:
        return ClockScene(self.config, self.app_dir)

    def get_active_scene(self) -> Scene:
        return ClockScene(self.config, self.app_dir)

    def get_scenes(self):
        return {"clock": ClockScene(self.config, self.app_dir)}
