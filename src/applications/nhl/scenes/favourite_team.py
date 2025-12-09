import math
import threading
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from tfeos.input import InputType, InputResult
from appkit.base import Scene
from appkit.graphics_helpers import crop_image, MatrixCanvas, Region

from .nhl_api import get_next_game, get_standings


class NHLFavouriteTeamScene(Scene):
    def __init__(self, application_config):
        self.config = application_config.config
        self.app_dir = application_config.app_dir
        self.last_update = None
        self.next_game_data = None
        self.team_stats = None
        self.show_stats = False

        self.matrix_canvas = MatrixCanvas()

        font_path = self.app_dir / "resources" / "fonts"
        self.fonts = {
            "sm": ImageFont.load(str(font_path / "Tamzen5x9r.pil")),
            "sm_bold": ImageFont.load(str(font_path / "Tamzen5x9b.pil")),
            "med": ImageFont.load(str(font_path / "Tamzen6x12r.pil")),
            "med_bold": ImageFont.load(str(font_path / "Tamzen6x12b.pil")),
            "lrg": ImageFont.load(str(font_path / "Tamzen8x15r.pil")),
            "lrg_bold": ImageFont.load(str(font_path / "Tamzen8x15b.pil")),
        }

        self.colours = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "grey_dark": (70, 70, 70),
            "grey_light": (180, 180, 180),
            "red": (255, 50, 50),
            "yellow": (255, 209, 0),
            "green": (28, 122, 0),
        }

        self.image_cache = {}

    def render(self, canvas) -> None:
        if not self.last_update or (datetime.now() - self.last_update).seconds > 300:
            fav_team = self.config.get("favourite_team", "MTL")
            self.next_game_data = get_next_game(fav_team)
            self._get_team_stats(fav_team)
            self.last_update = datetime.now()

        if not self.next_game_data:
            self.matrix_canvas.clear_region(Region.FULL)
            self.matrix_canvas.draw_text(
                Region.FULL, 2, 12, "No Data", self.colours["white"], self.fonts["sm"]
            )
            self.matrix_canvas.render_frame(canvas)
            return

        self.matrix_canvas.clear_region(Region.FULL)

        if self.show_stats:
            self._build_stats_image()
        else:
            self._build_next_game_image()

        self.matrix_canvas.render_frame(canvas)

    def _get_team_stats(self, team):
        standings = get_standings()

        for team_data in standings["league"]["leagues"]["NHL"]["teams"]:
            if team_data["team_abrv"] == team:
                self.team_stats = team_data
                return

    def _build_next_game_image(self):
        fav_team = self.config.get("favourite_team", "MTL")
        game = self.next_game_data

        self._add_team_logo(fav_team)

        self.matrix_canvas.draw_text(
            Region.FULL, 36, 0, "Next", self.colours["white"], self.fonts["med_bold"]
        )
        self.matrix_canvas.draw_line(
            Region.FULL, (34, 10), (60, 10), self.colours["white"]
        )

        if game["is_today"]:
            if game["has_started"]:
                self.matrix_canvas.draw_text(
                    Region.FULL, 38, 11, "IPR", self.colours["white"], self.fonts["med"]
                )
            else:
                time_str = game["start_datetime_local"].strftime("%H:%M")
                self._draw_time(time_str, 11)
        else:
            month = game["start_datetime_local"].strftime("%b")
            day = game["start_datetime_local"].strftime("%-d")
            month_col = 37 if len(day) == 1 else 35
            self.matrix_canvas.draw_text(
                Region.FULL, month_col, 12, month, self.colours["white"], self.fonts["sm"]
            )
            day_col = 53 if len(day) == 1 else 51
            self.matrix_canvas.draw_text(
                Region.FULL, day_col, 12, day, self.colours["white"], self.fonts["sm"]
            )

        if game["home_or_away"] == "home":
            self.matrix_canvas.draw_multichar_text(
                Region.FULL, [34, 38], 23, "VS", self.colours["white"], self.fonts["sm"]
            )
            self.matrix_canvas.draw_text(
                Region.FULL, 44, 21, game["opponent_abrv"], self.colours["white"], self.fonts["med_bold"]
            )
        else:
            self.matrix_canvas.draw_text(
                Region.FULL, 35, 21, "@", self.colours["white"], self.fonts["med"]
            )
            self.matrix_canvas.draw_text(
                Region.FULL, 43, 21, game["opponent_abrv"], self.colours["white"], self.fonts["med_bold"]
            )

    def _build_stats_image(self):
        fav_team = self.config.get("favourite_team", "MTL")

        self._add_team_logo(fav_team)

        self.matrix_canvas.draw_text(
            Region.FULL, 34, 0, "Stats", self.colours["white"], self.fonts["med_bold"]
        )
        self.matrix_canvas.draw_line(
            Region.FULL, (34, 10), (60, 10), self.colours["white"]
        )

        if self.team_stats:
            self.matrix_canvas.draw_text(
                Region.FULL,
                34,
                12,
                f"{self.team_stats['wins']}-{self.team_stats['losses']}-{self.team_stats['ot_losses']}",
                self.colours["white"],
                self.fonts["sm"],
            )
            self.matrix_canvas.draw_text(
                Region.FULL,
                34,
                20,
                f"Rk:{self.team_stats['rank']}",
                self.colours["white"],
                self.fonts["sm"],
            )

    def _draw_time(self, time_str, y_offset):
        if time_str[0] == "1":
            self.matrix_canvas.draw_time_display(
                Region.FULL, 36, y_offset, time_str, self.colours["white"], self.fonts["med"], 12, 4
            )
        else:
            self.matrix_canvas.draw_time_display(
                Region.FULL, 36, y_offset, time_str, self.colours["white"], self.fonts["med"], 8, 4
            )

    def _add_team_logo(self, team: str):
        logo_path = (
            self.app_dir / "resources" / "images" / "NHL" / "teams" / f"{team}.png"
        )
        if logo_path not in self.image_cache:
            if logo_path.exists():
                with Image.open(logo_path) as img:
                    self.image_cache[logo_path] = img.convert("RGB").copy()
        team_logo = self.image_cache[logo_path]
        team_logo = crop_image(team_logo)
        team_logo.thumbnail((30, 30))

        self.matrix_canvas.paste_image_centered(Region.FULL, team_logo, 30, 30, 1, 1)

    def handle_input(self, input_type: InputType):
        if input_type in [InputType.LEFT, InputType.RIGHT]:
            self.show_stats = not self.show_stats
