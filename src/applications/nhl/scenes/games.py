import math
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from appkit.base import Scene
from appkit.graphics_helpers import (clear_image, crop_image,
                                     set_image_on_canvas)

from .nhl_api import get_games


class NHLGamesScene(Scene):
    def __init__(self, config, app_dir: Path):
        super().__init__()
        self.config = config
        self.app_dir = app_dir
        self.data = {}
        self.current_game_index = 0
        self.last_game_change = time.time()
        self.last_update = None

        # Load fonts
        font_path = app_dir / "resources" / "fonts"
        self.FONTS = {
            "sm": ImageFont.load(str(font_path / "Tamzen5x9r.pil")),
            "sm_bold": ImageFont.load(str(font_path / "Tamzen5x9b.pil")),
            "med": ImageFont.load(str(font_path / "Tamzen6x12r.pil")),
            "med_bold": ImageFont.load(str(font_path / "Tamzen6x12b.pil")),
            "lrg": ImageFont.load(str(font_path / "Tamzen8x15r.pil")),
            "lrg_bold": ImageFont.load(str(font_path / "Tamzen8x15b.pil")),
        }

        # Colors
        self.COLOURS = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "grey_dark": (70, 70, 70),
            "grey_light": (180, 180, 180),
            "red": (255, 50, 50),
            "yellow": (255, 209, 0),
            "green": (28, 122, 0),
        }

        # Create images for composition
        self.images = {
            "left": Image.new("RGB", (40, 30)),
            "centre": Image.new("RGB", (20, 30)),
            "right": Image.new("RGB", (40, 30)),
            "full": Image.new("RGB", (64, 32)),
        }

        self.draw = {
            "left": ImageDraw.Draw(self.images["left"]),
            "centre": ImageDraw.Draw(self.images["centre"]),
            "right": ImageDraw.Draw(self.images["right"]),
            "full": ImageDraw.Draw(self.images["full"]),
        }

        self.LEAGUE = "NHL"

    def render(self, canvas) -> None:
        # Update game data every 60 seconds
        if not self.last_update or (datetime.now() - self.last_update).seconds > 60:
            self.data["games"] = get_games(date.today())
            self.last_update = datetime.now()

        games = self.data.get("games", [])

        if not games:
            self._build_no_games_image()
            set_image_on_canvas(canvas, self.images["full"])
            return

        # Auto-cycle through games every 4 seconds
        if time.time() - self.last_game_change > 4:
            self.current_game_index = (self.current_game_index + 1) % len(games)
            self.last_game_change = time.time()

        game = games[self.current_game_index]

        # Clear all images
        for img_key in ["left", "centre", "right", "full"]:
            clear_image(self.images[img_key], self.draw[img_key])

        # Build appropriate image based on game status
        if game["status"] in ["FUT", "PRE"]:
            self._build_game_not_started_image(game)
        elif game["status"] in ["LIVE", "CRIT"]:
            self._build_game_in_progress_image(game)
        elif game["status"] in ["OFF", "FINAL"]:
            self._build_game_complete_image(game)

        # Combine images and display
        self.images["full"].paste(self.images["left"], (-19, 1))
        self.images["full"].paste(self.images["centre"], (22, 1))
        self.images["full"].paste(self.images["right"], (43, 1))

        set_image_on_canvas(canvas, self.images["full"])

    def _build_no_games_image(self):
        clear_image(self.images["full"], self.draw["full"])
        self.draw["full"].text(
            (31, 0), "No", font=self.FONTS["med"], fill=self.COLOURS["white"]
        )
        self.draw["full"].text(
            (31, 10), "Games", font=self.FONTS["med"], fill=self.COLOURS["white"]
        )
        self.draw["full"].text(
            (31, 21),
            date.today().strftime("%b %-d"),
            font=self.FONTS["sm"],
            fill=self.COLOURS["white"],
        )

    def _build_game_not_started_image(self, game):
        self._add_team_logos_to_image(game)

        # Add "Today"
        self.draw["centre"].text(
            (0, -1), "T", font=self.FONTS["med"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (4, 1), "o", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (8, 1), "d", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (12, 1), "a", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (16, 1), "y", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )

        # Add @
        self.draw["centre"].text(
            (5, 7), "@", font=self.FONTS["lrg"], fill=self.COLOURS["white"]
        )

        # Add start time
        self._add_time_to_image(game)

    def _build_game_in_progress_image(self, game):
        self._add_team_logos_to_image(game)
        self._add_playing_period_to_image(game)

        if game["period_time_remaining"] and not game["is_intermission"]:
            self._add_time_to_image(game)

        self._add_score_to_image(game)

    def _build_game_complete_image(self, game):
        self._add_team_logos_to_image(game)

        # Add "Final"
        self.draw["centre"].text(
            (0, -1), "F", font=self.FONTS["med"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (4, 1), "i", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (8, 1), "n", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (13, 1), "a", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )
        self.draw["centre"].text(
            (16, 1), "l", font=self.FONTS["sm"], fill=self.COLOURS["white"]
        )

        self._add_score_to_image(game)

    def _add_team_logos_to_image(self, game):
        # Away logo (left)
        away_logo_path = (
            self.app_dir
            / "resources"
            / "images"
            / "NHL"
            / "teams"
            / f"{game['away_abrv']}.png"
        )
        if away_logo_path.exists():
            away_logo = Image.open(away_logo_path).convert("RGB")
            away_logo = crop_image(away_logo)
            away_logo.thumbnail(self.images["left"].size)

            away_x = self.images["left"].width - away_logo.width
            away_y = math.floor((self.images["left"].height - away_logo.height) / 2)
            self.images["left"].paste(away_logo, (away_x, away_y))

        # Home logo (right)
        home_logo_path = (
            self.app_dir
            / "resources"
            / "images"
            / "NHL"
            / "teams"
            / f"{game['home_abrv']}.png"
        )
        if home_logo_path.exists():
            home_logo = Image.open(home_logo_path).convert("RGB")
            home_logo = crop_image(home_logo)
            home_logo.thumbnail(self.images["right"].size)

            home_y = math.floor((self.images["right"].height - home_logo.height) / 2)
            self.images["right"].paste(home_logo, (0, home_y))

    def _add_score_to_image(self, game):
        away_score = str(game["away_score"] or 0)
        home_score = str(game["home_score"] or 0)

        if max(len(away_score), len(home_score)) == 1:
            self.draw["centre"].text(
                (8, 19), "-", font=self.FONTS["sm_bold"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (0, 16),
                away_score,
                font=self.FONTS["lrg_bold"],
                fill=self.COLOURS["white"],
            )
            self.draw["centre"].text(
                (12, 16),
                home_score,
                font=self.FONTS["lrg_bold"],
                fill=self.COLOURS["white"],
            )
        else:
            self.draw["centre"].text(
                (-1, 17), away_score, font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            home_x = 20 - (5 * len(home_score) - 1)
            self.draw["centre"].text(
                (home_x, 23),
                home_score,
                font=self.FONTS["sm"],
                fill=self.COLOURS["white"],
            )

    def _add_playing_period_to_image(self, game):
        if game["is_intermission"]:
            self.draw["centre"].text(
                (1, 7), "INT", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
            return

        period_num = game.get("period_num")
        period_type = game.get("period_type", "REG")

        if not period_num:
            return

        if period_type == "SO":
            self.draw["centre"].text(
                (4, -1), "SO", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
        elif period_type == "OT" and period_num == 4:
            self.draw["centre"].text(
                (4, -1), "OT", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
        elif period_type == "OT":
            ot_num = str(period_num - 3)
            self.draw["centre"].text(
                (1, -1),
                f"{ot_num}OT",
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
        elif period_num == 1:
            self.draw["centre"].text(
                (4, -1), "1", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (8, -1), "s", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (12, -1), "t", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
        elif period_num == 2:
            self.draw["centre"].text(
                (3, -1), "2", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (9, -1), "n", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (13, -1), "d", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
        elif period_num == 3:
            self.draw["centre"].text(
                (3, -1), "3", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (9, -1), "r", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            self.draw["centre"].text(
                (13, -1), "d", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )

    def _add_time_to_image(self, game):
        if game["has_started"]:
            time_str = game["period_time_remaining"]
            row_offset = 0
        else:
            time_str = game["start_datetime_local"].strftime("%H:%M")
            row_offset = 13

        if len(time_str) >= 5:
            if time_str[0] == "2":
                self.draw["centre"].text(
                    (0, 8 + row_offset),
                    time_str[0],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].text(
                    (4, 8 + row_offset),
                    time_str[1],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].point(
                    (9, 11 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].point(
                    (9, 13 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].text(
                    (11, 8 + row_offset),
                    time_str[3],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].text(
                    (15, 8 + row_offset),
                    time_str[4],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
            elif time_str[0] == "1":
                self.draw["centre"].text(
                    (-1, 8 + row_offset),
                    time_str[0],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].text(
                    (4, 8 + row_offset),
                    time_str[1],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].point(
                    (9, 11 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].point(
                    (9, 13 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].text(
                    (11, 8 + row_offset),
                    time_str[3],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].text(
                    (16, 8 + row_offset),
                    time_str[4],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
            else:
                self.draw["centre"].text(
                    (2, 8 + row_offset),
                    time_str[1],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].point(
                    (7, 11 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].point(
                    (7, 13 + row_offset), fill=self.COLOURS["white"]
                )
                self.draw["centre"].text(
                    (9, 8 + row_offset),
                    time_str[3],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )
                self.draw["centre"].text(
                    (14, 8 + row_offset),
                    time_str[4],
                    font=self.FONTS["sm"],
                    fill=self.COLOURS["white"],
                )

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            return "menu"
        elif input_type in ["left", "right"]:
            games = self.data.get("games", [])
            if games:
                if input_type == "right":
                    self.current_game_index = (self.current_game_index + 1) % len(games)
                else:
                    self.current_game_index = (self.current_game_index - 1) % len(games)
                self.last_game_change = time.time()
        return None
