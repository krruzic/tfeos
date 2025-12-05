from typing import Tuple

try:
    from rgbmatrix import graphics
except ImportError:
    graphics = None


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b
        if graphics:
            self._color = graphics.Color(r, g, b)

    @classmethod
    def from_hex(cls, hex_string: str) -> "Color":
        hex_string = hex_string.lstrip("#")
        if len(hex_string) == 6:
            r = int(hex_string[0:2], 16)
            g = int(hex_string[2:4], 16)
            b = int(hex_string[4:6], 16)
            return cls(r, g, b)
        raise ValueError(f"Invalid hex color: {hex_string}")


class Font:
    def __init__(self, font_path: str):
        if graphics:
            self._font = graphics.Font()
            self._font.LoadFont(font_path)
        self.font_path = font_path

    @property
    def height(self) -> int:
        if graphics and hasattr(self._font, "height"):
            return self._font.height
        return 0

    @property
    def baseline(self) -> int:
        if graphics and hasattr(self._font, "baseline"):
            return self._font.baseline
        return 0


def draw_text(canvas, font: Font, x: int, y: int, color: Color, text: str) -> int:
    if graphics:
        return graphics.DrawText(canvas, font._font, x, y, color._color, text)
    return 0


def draw_text_centered(
    canvas, font: Font, y: int, color: Color, text: str, canvas_width: int = 64
) -> int:
    if graphics:
        text_len = graphics.DrawText(canvas, font._font, 0, 0, color._color, text)
        x = (canvas_width - text_len) // 2
        return graphics.DrawText(canvas, font._font, x, y, color._color, text)
    return 0


def draw_circle(canvas, x: int, y: int, r: int, color: Color):
    if graphics:
        graphics.DrawCircle(canvas, x, y, r, color._color)


def draw_line(canvas, x1: int, y1: int, x2: int, y2: int, color: Color):
    if graphics:
        graphics.DrawLine(canvas, x1, y1, x2, y2, color._color)
