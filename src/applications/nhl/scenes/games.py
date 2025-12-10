import math
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from appkit.base import Scene
from appkit.graphics_helpers import MatrixCanvas, Region, crop_image
from tfeos.input import InputResult, InputType

from .nhl_api import get_games


class NHLGamesScene(Scene):
    def __init__(self, application_config):
        self.config = application_config.config
        self.app_dir = application_config.app_dir
        self.data = {}
        self.current_game_index = 0
        self.last_game_change = time.time()
        self.last_update = None
        self.image_cache = {}
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

    def render(self, canvas) -> None:
        if not self.last_update or (datetime.now() - self.last_update).seconds > 60:
            self.data["games"] = get_games(date.today())
            self.last_update = datetime.now()

        games = self.data.get("games", [])

        if not games:
            self._build_no_games_image()
            self.matrix_canvas.render_frame(canvas)
            return

        if time.time() - self.last_game_change > 4:
            self.current_game_index = (self.current_game_index + 1) % len(games)
            self.last_game_change = time.time()

        game = games[self.current_game_index]

        for region in [Region.LEFT, Region.CENTRE, Region.RIGHT, Region.FULL]:
            self.matrix_canvas.clear_region(region)

        if game["status"] in ["FUT", "PRE"]:
            self._build_game_not_started_image(game)
        elif game["status"] in ["LIVE", "CRIT"]:
            self._build_game_in_progress_image(game)
        elif game["status"] in ["OFF", "FINAL"]:
            self._build_game_complete_image(game)

        self.matrix_canvas.copy_region_to_full(Region.LEFT, -19, 1)
        self.matrix_canvas.copy_region_to_full(Region.CENTRE, 22, 1)
        self.matrix_canvas.copy_region_to_full(Region.RIGHT, 43, 1)

        self.matrix_canvas.render_frame(canvas)

    def _build_no_games_image(self):
        self.matrix_canvas.clear_region(Region.FULL)
        self.matrix_canvas.draw_text(
            Region.FULL, 31, 0, "No", self.colours["white"], self.fonts["med"]
        )
        self.matrix_canvas.draw_text(
            Region.FULL, 31, 10, "Games", self.colours["white"], self.fonts["med"]
        )
        self.matrix_canvas.draw_text(
            Region.FULL,
            31,
            21,
            date.today().strftime("%b %-d"),
            self.colours["white"],
            self.fonts["sm"],
        )

    def _build_game_not_started_image(self, game):
        self._add_team_logos_to_image(game)

        self.matrix_canvas.draw_text(
            Region.CENTRE, 0, -1, "T", self.colours["white"], self.fonts["med"]
        )

        self.matrix_canvas.draw_multichar_text(
            Region.CENTRE,
            [4, 8, 12, 16],
            1,
            "oday",
            self.colours["white"],
            self.fonts["sm"],
        )

        self.matrix_canvas.draw_text(
            Region.CENTRE, 5, 7, "@", self.colours["white"], self.fonts["lrg"]
        )

        self._add_time_to_image(game)

    def _build_game_in_progress_image(self, game):
        self._add_team_logos_to_image(game)
        self._add_playing_period_to_image(game)

        if game["period_time_remaining"] and not game["is_intermission"]:
            self._add_time_to_image(game)

        self._add_score_to_image(game)

    def _build_game_complete_image(self, game):
        self._add_team_logos_to_image(game)

        self.matrix_canvas.draw_multichar_text(
            Region.CENTRE,
            [0, 4, 8, 13, 16],
            -1,
            "Final",
            self.colours["white"],
            self.fonts["med"],
        )
        self.matrix_canvas.draw_multichar_text(
            Region.CENTRE,
            [4, 8, 13, 16],
            1,
            "inal",
            self.colours["white"],
            self.fonts["sm"],
        )

        self._add_score_to_image(game)

    def _add_team_logos_to_image(self, game):
        away_logo_path = (
            self.app_dir
            / "resources"
            / "images"
            / "NHL"
            / "teams"
            / f"{game['away_abrv']}.png"
        )
        if away_logo_path.exists():
            if away_logo_path not in self.image_cache:
                self.image_cache[away_logo_path] = Image.open(away_logo_path).convert(
                    "RGB"
                )
            away_logo = self.image_cache[away_logo_path].copy()
            away_logo = crop_image(away_logo)
            away_logo.thumbnail((30, 30))

            away_x = 40 - away_logo.width
            away_y = (30 - away_logo.height) // 2
            self.matrix_canvas.draw_image(Region.LEFT, away_x, away_y, away_logo)

        home_logo_path = (
            self.app_dir
            / "resources"
            / "images"
            / "NHL"
            / "teams"
            / f"{game['home_abrv']}.png"
        )
        if home_logo_path.exists():
            if home_logo_path not in self.image_cache:
                self.image_cache[home_logo_path] = Image.open(home_logo_path).convert(
                    "RGB"
                )
            home_logo = self.image_cache[home_logo_path].copy()
            home_logo = crop_image(home_logo)
            home_logo.thumbnail((30, 30))

            home_y = (30 - home_logo.height) // 2
            self.matrix_canvas.draw_image(Region.RIGHT, 0, home_y, home_logo)

    def _add_score_to_image(self, game):
        away_score = str(game["away_score"] or 0)
        home_score = str(game["home_score"] or 0)

        self.matrix_canvas.draw_score_pair(
            Region.CENTRE,
            0,
            16,
            away_score,
            home_score,
            self.colours["white"],
            self.fonts["lrg_bold"],
            self.fonts["sm_bold"],
        )

    def _add_playing_period_to_image(self, game):
        if game["is_intermission"]:
            self.matrix_canvas.draw_text(
                Region.CENTRE, 1, 7, "INT", self.colours["white"], self.fonts["med"]
            )
            return

        period_num = game.get("period_num")
        period_type = game.get("period_type", "REG")

        if not period_num:
            return

        if period_type == "SO":
            self.matrix_canvas.draw_text(
                Region.CENTRE, 4, -1, "SO", self.colours["white"], self.fonts["med"]
            )
        elif period_type == "OT" and period_num == 4:
            self.matrix_canvas.draw_text(
                Region.CENTRE, 4, -1, "OT", self.colours["white"], self.fonts["med"]
            )
        elif period_type == "OT":
            ot_num = str(period_num - 3)
            self.matrix_canvas.draw_text(
                Region.CENTRE,
                1,
                -1,
                f"{ot_num}OT",
                self.colours["white"],
                self.fonts["med"],
            )
        elif period_num == 1:
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE, [4], -1, "1", self.colours["white"], self.fonts["med"]
            )
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE,
                [8, 12],
                -1,
                "st",
                self.colours["white"],
                self.fonts["sm"],
            )
        elif period_num == 2:
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE, [3], -1, "2", self.colours["white"], self.fonts["med"]
            )
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE,
                [9, 13],
                -1,
                "nd",
                self.colours["white"],
                self.fonts["sm"],
            )
        elif period_num == 3:
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE, [3], -1, "3", self.colours["white"], self.fonts["med"]
            )
            self.matrix_canvas.draw_multichar_text(
                Region.CENTRE,
                [9, 13],
                -1,
                "rd",
                self.colours["white"],
                self.fonts["sm"],
            )

    def _add_time_to_image(self, game):
        if game["has_started"]:
            time_str = game["period_time_remaining"]
            row_offset = 0
        else:
            time_str = game["start_datetime_local"].strftime("%H:%M")
            row_offset = 13

        self.matrix_canvas.draw_time_display(
            Region.CENTRE,
            0,
            8 + row_offset,
            time_str,
            self.colours["white"],
            self.fonts["sm"],
        )

    def handle_input(self, input_type: InputType):
        if input_type in [InputType.LEFT, InputType.RIGHT]:
            games = self.data.get("games", [])
            if games:
                if input_type == InputType.RIGHT:
                    self.current_game_index = (self.current_game_index + 1) % len(games)
                else:
                    self.current_game_index = (self.current_game_index - 1) % len(games)
                self.last_game_change = time.time()
