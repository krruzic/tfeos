import random
import time
from collections import deque
from pathlib import Path
from typing import Optional

from appkit.base import Application, Scene
from appkit.config import Config
from appkit.graphics_helpers import Color


class SnakeScene(Scene):
    def __init__(self, config, app_dir: Path):
        super().__init__()
        self.config = config
        self.app_dir = app_dir
        self.reset_game()

    def reset_game(self):
        self.snake = deque([(32, 16), (31, 16), (30, 16)])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self._spawn_food()
        self.game_over = False
        self.won = False
        self.last_move = time.time()
        self.move_delay = 0.15

    def _spawn_food(self):
        while True:
            food = (random.randint(0, 63), random.randint(0, 31))
            if food not in self.snake:
                return food

    def render(self, canvas) -> None:
        canvas.Clear()

        # Draw background (light brown)
        for y in range(32):
            for x in range(64):
                canvas.SetPixel(x, y, 101, 67, 33)

        # Draw snake (green)
        for segment in self.snake:
            canvas.SetPixel(segment[0], segment[1], 0, 255, 0)

        # Draw food (red)
        canvas.SetPixel(self.food[0], self.food[1], 255, 0, 0)

        # Game logic
        if not self.game_over and not self.won:
            if time.time() - self.last_move > self.move_delay:
                self._move_snake()
                self.last_move = time.time()

        # Draw game over/win message
        if self.game_over:
            self._draw_text_overlay(canvas, "GAME", "OVER")
        elif self.won:
            self._draw_text_overlay(canvas, "YOU", "WIN!")

    def _move_snake(self):
        self.direction = self.next_direction

        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Check collision with walls
        if new_head[0] < 0 or new_head[0] >= 64 or new_head[1] < 0 or new_head[1] >= 32:
            self.game_over = True
            return

        # Check collision with self
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.appendleft(new_head)

        # Check if ate food
        if new_head == self.food:
            # Check if won (2048 segments)
            if len(self.snake) >= 2048:
                self.won = True
                return
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def _draw_text_overlay(self, canvas, line1, line2):
        # Simple pixel text overlay
        # Draw semi-transparent background
        for y in range(10, 22):
            for x in range(16, 48):
                canvas.SetPixel(x, y, 0, 0, 0)

        # Draw text (simplified - just show the message centered)
        self._draw_simple_text(canvas, line1, 20, 12)
        self._draw_simple_text(canvas, line2, 20, 18)

    def _draw_simple_text(self, canvas, text, x, y):
        # Very basic 3x5 pixel font
        char_width = 4
        for i, char in enumerate(text):
            char_x = x + (i * char_width)
            self._draw_char(canvas, char, char_x, y)

    def _draw_char(self, canvas, char, x, y):
        # Minimal character rendering - just draw white pixels
        patterns = {
            "G": [
                (0, 0),
                (1, 0),
                (2, 0),
                (0, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (0, 4),
                (1, 4),
                (2, 4),
            ],
            "A": [
                (1, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (1, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (2, 4),
            ],
            "M": [
                (0, 0),
                (2, 0),
                (0, 1),
                (1, 1),
                (2, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (2, 4),
            ],
            "E": [
                (0, 0),
                (1, 0),
                (2, 0),
                (0, 1),
                (0, 2),
                (1, 2),
                (0, 3),
                (0, 4),
                (1, 4),
                (2, 4),
            ],
            "O": [
                (0, 0),
                (1, 0),
                (2, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (1, 4),
                (2, 4),
            ],
            "V": [
                (0, 0),
                (2, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (1, 4),
            ],
            "R": [
                (0, 0),
                (1, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (1, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (2, 4),
            ],
            "Y": [(0, 0), (2, 0), (0, 1), (2, 1), (1, 2), (1, 3), (1, 4)],
            "U": [
                (0, 0),
                (2, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (1, 4),
            ],
            "W": [
                (0, 0),
                (2, 0),
                (0, 1),
                (2, 1),
                (0, 2),
                (1, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (2, 4),
            ],
            "I": [
                (0, 0),
                (1, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (1, 3),
                (0, 4),
                (1, 4),
                (2, 4),
            ],
            "N": [
                (0, 0),
                (2, 0),
                (0, 1),
                (1, 1),
                (2, 1),
                (0, 2),
                (2, 2),
                (0, 3),
                (2, 3),
                (0, 4),
                (2, 4),
            ],
            "!": [(1, 0), (1, 1), (1, 2), (1, 4)],
        }

        pattern = patterns.get(char.upper(), [])
        for px, py in pattern:
            if 0 <= x + px < 64 and 0 <= y + py < 32:
                canvas.SetPixel(x + px, y + py, 255, 255, 255)

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            return "menu"

        if self.game_over or self.won:
            if input_type == "accept":
                self.reset_game()
            return None

        # Change direction (can't reverse)
        if input_type == "up" and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif input_type == "down" and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif input_type == "left" and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif input_type == "right" and self.direction != (-1, 0):
            self.next_direction = (1, 0)

        return None


class App(Application):
    def get_framerate(self) -> int:
        return 30

    def on_config_changed(self, new_config: Config) -> None:
        return

    def get_scenes(self):
        return {"snake": SnakeScene(self.config, self.app_dir)}

    def get_active_scene(self) -> Scene:
        return SnakeScene(self.config, self.app_dir)

    def default_scene(self) -> Scene:
        return SnakeScene(self.config, self.app_dir)
