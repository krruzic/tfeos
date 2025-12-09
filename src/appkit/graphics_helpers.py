from PIL import Image, ImageDraw, ImageFont
from enum import Enum
from typing import Dict, List, Tuple, Optional


class Region(Enum):
    LEFT = 1
    CENTRE = 2
    RIGHT = 3
    FULL = 4


class MatrixCanvas:
    def __init__(self):
        self.last_frame = None
        self.sub_images = {
            Region.LEFT: Image.new("RGB", (40, 30)),
            Region.CENTRE: Image.new("RGB", (20, 30)),
            Region.RIGHT: Image.new("RGB", (40, 30)),
            Region.FULL: Image.new("RGB", (64, 32)),
        }

        self.draw_regions: Dict[Region, ImageDraw.ImageDraw] = {
            Region.LEFT: ImageDraw.Draw(self.sub_images[Region.LEFT]),
            Region.CENTRE: ImageDraw.Draw(self.sub_images[Region.CENTRE]),
            Region.RIGHT: ImageDraw.Draw(self.sub_images[Region.RIGHT]),
            Region.FULL: ImageDraw.Draw(self.sub_images[Region.FULL]),
        }

    def draw_text(
        self,
        region: Region,
        x: int,
        y: int,
        text: str,
        color,
        font: ImageFont.ImageFont,
    ):
        self.draw_regions[region].text((x, y), text, font=font, fill=color)

    def draw_point(self, region: Region, x: int, y: int, color):
        self.draw_regions[region].point((x, y), fill=color)

    def draw_line(self, region: Region, start: Tuple[int, int], end: Tuple[int, int], color):
        self.draw_regions[region].line([start, end], fill=color)

    def draw_image(self, region: Region, x: int, y: int, image: Image.Image):
        self.sub_images[region].paste(image, (x, y))

    def draw_multichar_text(
        self,
        region: Region,
        x_positions: List[int],
        y: int,
        text: str,
        color,
        font: ImageFont.ImageFont,
    ):
        for i, char in enumerate(text):
            if i < len(x_positions):
                self.draw_text(region, x_positions[i], y, char, color, font)

    def draw_time_display(
        self,
        region: Region,
        x: int,
        y: int,
        time_str: str,
        color,
        font: ImageFont.ImageFont,
        colon_offset_x: int = 6,
        colon_offset_y: int = 3,
    ):
        """Draw time in HH:MM or H:MM format with colon as dots"""
        if len(time_str) < 5:
            return

        if time_str[0] == "2":
            self.draw_text(region, x, y, time_str[0], color, font)
            self.draw_text(region, x + 4, y, time_str[1], color, font)
            self.draw_point(region, x + 9, y + colon_offset_y, color)
            self.draw_point(region, x + 9, y + colon_offset_y + 2, color)
            self.draw_text(region, x + 11, y, time_str[3], color, font)
            self.draw_text(region, x + 15, y, time_str[4], color, font)
        elif time_str[0] == "1":
            self.draw_text(region, x - 1, y, time_str[0], color, font)
            self.draw_text(region, x + 4, y, time_str[1], color, font)
            self.draw_point(region, x + 9, y + colon_offset_y, color)
            self.draw_point(region, x + 9, y + colon_offset_y + 2, color)
            self.draw_text(region, x + 11, y, time_str[3], color, font)
            self.draw_text(region, x + 16, y, time_str[4], color, font)
        else:
            self.draw_text(region, x + 2, y, time_str[1], color, font)
            self.draw_point(region, x + 7, y + colon_offset_y, color)
            self.draw_point(region, x + 7, y + colon_offset_y + 2, color)
            self.draw_text(region, x + 9, y, time_str[3], color, font)
            self.draw_text(region, x + 14, y, time_str[4], color, font)

    def draw_centered_text(
        self,
        region: Region,
        y: int,
        text: str,
        color,
        font: ImageFont.ImageFont,
    ):
        bbox = self.draw_regions[region].textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        region_width = self.sub_images[region].width
        x = (region_width - text_width) // 2
        self.draw_text(region, x, y, text, color, font)

    def draw_score_pair(
        self,
        region: Region,
        x: int,
        y: int,
        away_score: str,
        home_score: str,
        color,
        font_large: ImageFont.ImageFont,
        font_small: ImageFont.ImageFont,
    ):
        """Draw score pair with dash separator, adjusting for digit count"""
        if max(len(away_score), len(home_score)) == 1:
            self.draw_text(region, x + 8, y + 3, "-", color, font_small)
            self.draw_text(region, x, y, away_score, color, font_large)
            self.draw_text(region, x + 12, y, home_score, color, font_large)
        else:
            self.draw_text(region, x - 1, y + 1, away_score, color, font_small)
            home_x = x + 20 - (5 * len(home_score) - 1)
            self.draw_text(region, home_x, y + 7, home_score, color, font_small)

    def paste_image_centered(
        self,
        region: Region,
        image: Image.Image,
        area_width: int,
        area_height: int,
        offset_x: int = 0,
        offset_y: int = 0,
    ):
        """Paste image centered within specified area"""
        x = offset_x + (area_width - image.width) // 2
        y = offset_y + (area_height - image.height) // 2
        self.draw_image(region, x, y, image)

    def draw_vertical_text(
        self,
        region: Region,
        x: int,
        y: int,
        text: str,
        color,
        font: ImageFont.ImageFont,
        bg_color,
    ):
        """Draw text vertically (rotated 90 degrees)"""
        bbox = self.draw_regions[region].textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        tmp_img = Image.new("RGB", (text_width, text_height))
        tmp_draw = ImageDraw.Draw(tmp_img)
        tmp_draw.rectangle([(0, 0), (text_width, text_height)], fill=bg_color)
        tmp_draw.text((0, 0), text, font=font, fill=color)
        tmp_img = tmp_img.rotate(90, expand=True)
        self.draw_image(region, x, y, tmp_img)

    def clear_region(self, region: Region, color=(0, 0, 0)):
        """Clear a region to specified color"""
        self.draw_regions[region].rectangle(
            [(0, 0), (self.sub_images[region].width, self.sub_images[region].height)],
            fill=color,
        )

    def copy_region_to_full(self, region: Region, x: int, y: int):
        self.sub_images[Region.FULL].paste(self.sub_images[region], (x, y))

    def render_frame(self, canvas):
        image_rgb = self.sub_images[Region.FULL]
        for y in range(min(self.sub_images[Region.FULL].height, 32)):
            for x in range(min(self.sub_images[Region.FULL].width, 64)):
                r, g, b = image_rgb.getpixel((x, y))
                canvas.SetPixel(x, y, r, g, b)

    def clear_full_image(self, region: Region):
        self.clear_region(region)

    def clear_partial_image(self, width: int, height: int, region: Region):
        """Clear an image to black"""
        self.draw_regions[region].rectangle([(0, 0), (width, height)], fill=(0, 0, 0))


def crop_image(image: Image.Image) -> Image.Image:
    """Crop transparent pixels from image"""
    if image.mode != "RGBA":
        return image

    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox)
    return image



# Legacy, don't use. Prefer PIL
try:
    from rgbmatrix import graphics
except ImportError:
    from RGBMatrixEmulator import graphics
    
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
        # Create a temporary color at (0,0) to measure, then clear that pixel
        text_len = graphics.DrawText(canvas, font._font, 0, -100, color._color, text)
        x = (canvas_width - text_len) // 2
        return graphics.DrawText(canvas, font._font, x, y, color._color, text)
    return 0


def draw_circle(canvas, x: int, y: int, r: int, color: Color):
    if graphics:
        graphics.DrawCircle(canvas, x, y, r, color._color)


def draw_line(canvas, x1: int, y1: int, x2: int, y2: int, color: Color):
    if graphics:
        graphics.DrawLine(canvas, x1, y1, x2, y2, color._color)