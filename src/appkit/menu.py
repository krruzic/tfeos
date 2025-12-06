import base64
import logging
from io import BytesIO
from typing import List, Optional

from .base import Scene
from .graphics_helpers import Color

logger = logging.getLogger("tfeos.menu")


class AppMenuItem:
    def __init__(self, name: str, display_name: str, icon_data: Optional[bytes]):
        self.name = name
        self.display_name = display_name
        self.icon_data = icon_data


class AppMenuScene(Scene):
    def __init__(self, apps: List[AppMenuItem]):
        self.apps = apps
        self.selected_index = 0
        self.icon_size = 16
        self.gap = 1

    @property
    def current_page(self) -> int:
        return self.selected_index // 6

    @property
    def total_pages(self) -> int:
        return (len(self.apps) + 5) // 6

    @property
    def position_on_page(self) -> tuple:
        """Returns (row, col) of selected icon on current page"""
        pos = self.selected_index % 6
        return (pos // 3, pos % 3)

    def render(self, canvas) -> None:
        canvas.Clear()

        start_idx = self.current_page * 6
        end_idx = min(start_idx + 6, len(self.apps))
        page_apps = self.apps[start_idx:end_idx]

        for idx, app in enumerate(page_apps):
            row = idx // 3
            col = idx % 3

            x = col * (self.icon_size + self.gap)
            y = row * (self.icon_size + self.gap)

            global_idx = start_idx + idx
            is_selected = global_idx == self.selected_index

            if app.icon_data:
                self._draw_icon(canvas, x, y, app.icon_data)
            else:
                self._draw_placeholder(canvas, x, y)

            if is_selected:
                self._draw_selection_border(canvas, x, y)

        self._draw_page_indicator(canvas)

    def _draw_icon(self, canvas, x: int, y: int, icon_data: bytes):
        try:
            from PIL import Image

            icon = Image.open(BytesIO(icon_data))
            icon = icon.convert("RGB")
            icon = icon.resize((self.icon_size, self.icon_size))

            for py in range(self.icon_size):
                for px in range(self.icon_size):
                    r, g, b = icon.getpixel((px, py))
                    canvas.SetPixel(x + px, y + py, r, g, b)
        except Exception:
            self._draw_placeholder(canvas, x, y)

    def _draw_placeholder(self, canvas, x: int, y: int):
        color = Color(64, 64, 64)
        for py in range(self.icon_size):
            for px in range(self.icon_size):
                if (
                    px == 0
                    or px == self.icon_size - 1
                    or py == 0
                    or py == self.icon_size - 1
                ):
                    canvas.SetPixel(x + px, y + py, color.r, color.g, color.b)

    def _draw_selection_border(self, canvas, x: int, y: int):
        color = Color(255, 255, 0)
        for i in range(self.icon_size):
            canvas.SetPixel(x + i, y, color.r, color.g, color.b)
            canvas.SetPixel(x + i, y + self.icon_size - 1, color.r, color.g, color.b)
            canvas.SetPixel(x, y + i, color.r, color.g, color.b)
            canvas.SetPixel(x + self.icon_size - 1, y + i, color.r, color.g, color.b)

    def _draw_page_indicator(self, canvas):
        indicator_x = 63
        indicator_size = 4
        total_height = self.total_pages * indicator_size + (self.total_pages - 1)
        start_y = (32 - total_height) // 2

        for page in range(self.total_pages):
            y = start_y + page * (indicator_size + 1)

            if page == self.current_page:
                color = Color(255, 255, 255)
            else:
                color = Color(64, 64, 64)

            for py in range(indicator_size):
                for px in range(indicator_size):
                    canvas.SetPixel(
                        indicator_x - indicator_size + px,
                        y + py,
                        color.r,
                        color.g,
                        color.b,
                    )

    def handle_input(self, input_type: str) -> Optional[str]:
        row, col = self.position_on_page

        if input_type == "down":
            if row < 1:
                new_index = self.selected_index + 3
                if new_index < len(self.apps):
                    self.selected_index = new_index
            else:
                new_page_start = (self.current_page + 1) * 6
                if new_page_start < len(self.apps):
                    self.selected_index = new_page_start

        elif input_type == "up":
            if row > 0:
                self.selected_index = max(0, self.selected_index - 3)
            else:
                if self.current_page > 0:
                    prev_page_start = (self.current_page - 1) * 6
                    self.selected_index = min(prev_page_start + 3, len(self.apps) - 1)

        elif input_type == "right":
            if col < 2:
                new_index = self.selected_index + 1
                page_end = min((self.current_page + 1) * 6, len(self.apps))
                if new_index < page_end:
                    self.selected_index = new_index
            else:
                page_start = self.current_page * 6
                target = page_start + (row * 3)
                if target < len(self.apps):
                    self.selected_index = target

        elif input_type == "left":
            if col > 0:
                self.selected_index -= 1
            else:
                page_start = self.current_page * 6
                page_end = min((self.current_page + 1) * 6, len(self.apps))
                target = min(page_start + (row * 3) + 2, page_end - 1)
                self.selected_index = target

        elif input_type == "accept":
            if self.selected_index < len(self.apps):
                return self.apps[self.selected_index].name

        return None
