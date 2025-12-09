from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

from appkit.base import Application, Scene, ApplicationConfig
from appkit.config import Config
from appkit.graphics_helpers import Color, Font, draw_text_centered
from tfeos.input import InputResult, InputType


class ClockScene(Scene):
    def __init__(self, application_config):
        self.config = application_config.config
        self.app_dir = application_config.app_dir

        font_path = self.app_dir / "resources" / "7x13.bdf"
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
    def __init__(self, application_config: ApplicationConfig, matrix):
        super().__init__(application_config, matrix)
        self.scenes = {"clock": ClockScene(self.application_config)}
        self.scene = self.scenes["clock"]
        self.scene_order = ["clock"]
        self.current_scene_index = 0

    def get_framerate(self) -> int:
        return 1

    def _render(self, canvas) -> None:
        self.scene.render(canvas)

    def _handle_input(self, input_type: InputType) -> Optional[InputResult]:
        return None

    def handle_new_config(self, new_config: Config) -> None:
        return
