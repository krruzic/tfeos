from datetime import datetime
from pathlib import Path
from typing import Optional

from appkit.base import Application, Scene
from appkit.graphics_helpers import Color, Font, draw_text_centered


class ClockScene(Scene):
    def __init__(self, config):
        self.config = config
        self.font = Font("/usr/share/fonts/misc/7x13.bdf")

    def render(self, canvas) -> None:
        canvas.Clear()

        now = datetime.now()
        if self.config.get("show_seconds", True):
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%H:%M")

        color_hex = self.config.get("color", "#ffffff")
        color = Color.from_hex(color_hex)

        y_pos = 16 + self.font.baseline
        draw_text_centered(canvas, self.font, y_pos, color, time_str)

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "back":
            return "menu"
        return None


class App(Application):
    def get_scenes(self):
        return {"clock": ClockScene(self.config)}
