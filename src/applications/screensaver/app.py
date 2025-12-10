import math
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from appkit.base import Application, ApplicationConfig, Scene
from appkit.config import Config
from appkit.graphics_helpers import Color
from tfeos.input import InputResult, InputType


class RainbowParasolScene(Scene):
    def __init__(self):
        self.angle = 0

    def render(self, canvas) -> None:
        canvas.Clear()
        center_x, center_y = 32, 16

        for y in range(32):
            for x in range(64):
                dx = x - center_x
                dy = y - center_y

                pixel_angle = math.degrees(math.atan2(dy, dx)) + 180
                pixel_angle = (pixel_angle + self.angle) % 360

                # Smooth gradient using HSV
                hue = pixel_angle / 360.0

                # Convert HSV to RGB (S=1, V=1 for full saturation/brightness)
                h = hue * 6.0
                c = 1.0
                x_val = 1.0 - abs((h % 2) - 1.0)

                if h < 1:
                    r, g, b = c, x_val, 0
                elif h < 2:
                    r, g, b = x_val, c, 0
                elif h < 3:
                    r, g, b = 0, c, x_val
                elif h < 4:
                    r, g, b = 0, x_val, c
                elif h < 5:
                    r, g, b = x_val, 0, c
                else:
                    r, g, b = c, 0, x_val

                # Scale to 0-255 and snap to 6-bit
                r = int(r * 252) & 0xFC
                g = int(g * 252) & 0xFC
                b = int(b * 252) & 0xFC

                canvas.SetPixel(x, y, r, g, b)

        self.angle = (self.angle + 5) % 360


class MatrixRainScene(Scene):
    def __init__(self):
        self.drops = []
        for x in range(64):
            self.drops.append(
                {
                    "x": x,
                    "y": random.randint(-32, 0),
                    "speed": random.randint(1, 3),
                    "length": random.randint(5, 15),
                }
            )

    def render(self, canvas) -> None:
        canvas.Clear()

        for drop in self.drops:
            for i in range(drop["length"]):
                y = drop["y"] - i
                if 0 <= y < 32:
                    brightness = int(255 * (1 - i / drop["length"]))
                    canvas.SetPixel(drop["x"], y, 0, brightness, 0)

            drop["y"] += drop["speed"]
            if drop["y"] - drop["length"] > 32:
                drop["y"] = random.randint(-32, -5)
                drop["speed"] = random.randint(1, 3)
                drop["length"] = random.randint(5, 15)


class StarfieldScene(Scene):
    def __init__(self):
        self.stars = []
        for _ in range(30):
            self.stars.append(
                {
                    "x": random.randint(0, 63),
                    "y": random.randint(0, 31),
                    "z": random.uniform(0.1, 1.0),
                    "brightness": random.randint(128, 255),
                }
            )

    def render(self, canvas) -> None:
        canvas.Clear()

        for star in self.stars:
            star["z"] -= 0.02
            if star["z"] <= 0:
                star["z"] = 1.0
                star["x"] = random.randint(0, 63)
                star["y"] = random.randint(0, 31)
                star["brightness"] = random.randint(128, 255)

            screen_x = int(32 + (star["x"] - 32) / star["z"])
            screen_y = int(16 + (star["y"] - 16) / star["z"])

            if 0 <= screen_x < 64 and 0 <= screen_y < 32:
                brightness = int(star["brightness"] * (1 - star["z"]))
                canvas.SetPixel(screen_x, screen_y, brightness, brightness, brightness)


class PlasmaScene(Scene):
    def __init__(self):
        self.time = 0

    def render(self, canvas) -> None:
        canvas.Clear()

        for y in range(32):
            for x in range(64):
                value = math.sin(x / 8.0 + self.time)
                value += math.sin(y / 6.0 + self.time)
                value += math.sin((x + y) / 10.0 + self.time)
                value += math.sin(math.sqrt(x * x + y * y) / 8.0 + self.time)
                value = (value + 4) / 8

                r, g, b = self._value_to_color(value)
                canvas.SetPixel(x, y, r, g, b)

        self.time += 0.1

    def _value_to_color(self, value):
        hue = value % 1.0
        r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
        return r, g, b

    def _hsv_to_rgb(self, h, s, v):
        if s == 0.0:
            return int(v * 255), int(v * 255), int(v * 255)
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if i == 0:
            return int(v * 255), int(t * 255), int(p * 255)
        if i == 1:
            return int(q * 255), int(v * 255), int(p * 255)
        if i == 2:
            return int(p * 255), int(v * 255), int(t * 255)
        if i == 3:
            return int(p * 255), int(q * 255), int(v * 255)
        if i == 4:
            return int(t * 255), int(p * 255), int(v * 255)
        return int(v * 255), int(p * 255), int(q * 255)


class ConwayLifeScene(Scene):
    def __init__(self):
        self.grid = [[random.choice([0, 1]) for _ in range(64)] for _ in range(32)]
        self.generation = 0
        self.last_update = time.time()

    def render(self, canvas) -> None:
        canvas.Clear()

        # Draw current generation
        for y in range(32):
            for x in range(64):
                if self.grid[y][x]:
                    canvas.SetPixel(x, y, 0, 255, 0)

        # Update every 0.2 seconds
        if time.time() - self.last_update > 0.2:
            self._next_generation()
            self.last_update = time.time()
            self.generation += 1

            # Reset if stagnant (every 200 generations)
            if self.generation > 200:
                self.grid = [
                    [random.choice([0, 1]) for _ in range(64)] for _ in range(32)
                ]
                self.generation = 0

    def _next_generation(self):
        new_grid = [[0 for _ in range(64)] for _ in range(32)]

        for y in range(32):
            for x in range(64):
                neighbors = self._count_neighbors(x, y)

                if self.grid[y][x]:
                    # Cell is alive
                    if neighbors in [2, 3]:
                        new_grid[y][x] = 1
                else:
                    # Cell is dead
                    if neighbors == 3:
                        new_grid[y][x] = 1

        self.grid = new_grid

    def _count_neighbors(self, x, y):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % 64
                ny = (y + dy) % 32
                count += self.grid[ny][nx]
        return count


class ScreensaverManager(Scene):
    def __init__(self):
        self.scenes = [
            RainbowParasolScene(),
            MatrixRainScene(),
            StarfieldScene(),
            PlasmaScene(),
            ConwayLifeScene(),
        ]
        self.current_index = 0

    def render(self, canvas) -> None:
        self.scenes[self.current_index].render(canvas)

    def handle_input(self, input_type: InputType) -> None:
        if input_type == InputType.RIGHT:
            self.current_index = (self.current_index + 1) % len(self.scenes)
        elif input_type == InputType.LEFT:
            self.current_index = (self.current_index - 1) % len(self.scenes)
        return None


class App(Application):
    def __init__(self, application_config: ApplicationConfig, matrix):
        super().__init__(application_config, matrix)
        self.screensaver = ScreensaverManager()

    def get_framerate(self) -> int:
        return 30

    def _render(self, canvas) -> None:
        self.screensaver.render(canvas)

    def _handle_input(self, input_type: InputType) -> Optional[InputResult]:
        self.screensaver.handle_input(input_type)

    def handle_new_config(self, new_config: Config):
        return
