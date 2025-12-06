import math
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from appkit.base import Scene
from appkit.graphics_helpers import (clear_image, crop_image,
                                     set_image_on_canvas)

from .nhl_api import get_next_game, get_standings


class NHLNextGameScene(Scene):
    def __init__(self, config, app_dir: Path):
        super().__init__()
        self.config = config
        self.app_dir = app_dir
        self.last_update = None
        self.next_game_data = None
        self.team_stats = None
        self.show_stats = False

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

        # Create images
        self.images = {"full": Image.new("RGB", (64, 32))}

        self.draw = {"full": ImageDraw.Draw(self.images["full"])}

        self.LEAGUE = "NHL"

    def render(self, canvas) -> None:
        # Update data every 5 minutes
        if not self.last_update or (datetime.now() - self.last_update).seconds > 300:
            fav_team = self.config.get("favourite_team", "MTL")
            self.next_game_data = get_next_game(fav_team)
            self._get_team_stats(fav_team)
            self.last_update = datetime.now()

        if not self.next_game_data:
            clear_image(self.images["full"], self.draw["full"])
            self.draw["full"].text(
                (2, 12), "No Data", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            set_image_on_canvas(canvas, self.images["full"])
            return

        clear_image(self.images["full"], self.draw["full"])

        if self.show_stats:
            self._build_stats_image()
        else:
            self._build_next_game_image()

        set_image_on_canvas(canvas, self.images["full"])

    def _get_team_stats(self, team):
        """Get team stats from standings data"""
        standings = get_standings()

        # Find team in league standings
        for team_data in standings["league"]["leagues"]["NHL"]["teams"]:
            if team_data["team_abrv"] == team:
                self.team_stats = team_data
                return

    def _build_next_game_image(self):
        fav_team = self.config.get("favourite_team", "MTL")
        game = self.next_game_data

        # Add team logo
        self._add_team_logo(fav_team)

        # Add "Next" and line
        self.draw["full"].text(
            (36, 0), "Next", font=self.FONTS["med_bold"], fill=self.COLOURS["white"]
        )
        self.draw["full"].line([(34, 10), (60, 10)], fill=self.COLOURS["white"])

        # If game is today
        if game["is_today"]:
            if game["has_started"]:
                self.draw["full"].text(
                    (38, 11), "IPR", font=self.FONTS["med"], fill=self.COLOURS["white"]
                )
            else:
                time_str = game["start_datetime_local"].strftime("%I:%M")
                self._draw_time(time_str, 11)
        else:
            # Draw date
            month = game["start_datetime_local"].strftime("%b")
            day = game["start_datetime_local"].strftime("%-d")
            month_col = 37 if len(day) == 1 else 35
            self.draw["full"].text(
                (month_col, 12),
                month,
                font=self.FONTS["sm"],
                fill=self.COLOURS["white"],
            )
            day_col = 53 if len(day) == 1 else 51
            self.draw["full"].text(
                (day_col, 12), day, font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )

        # Add VS/@ and opponent
        if game["home_or_away"] == "home":
            self.draw["full"].text(
                (34, 23), "V", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            self.draw["full"].text(
                (38, 23), "S", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            self.draw["full"].text(
                (44, 21),
                game["opponent_abrv"],
                font=self.FONTS["med_bold"],
                fill=self.COLOURS["white"],
            )
        else:
            self.draw["full"].text(
                (35, 21), "@", font=self.FONTS["med"], fill=self.COLOURS["white"]
            )
            self.draw["full"].text(
                (43, 21),
                game["opponent_abrv"],
                font=self.FONTS["med_bold"],
                fill=self.COLOURS["white"],
            )

    def _build_stats_image(self):
        fav_team = self.config.get("favourite_team", "MTL")

        # Add team logo
        self._add_team_logo(fav_team)

        # Add "Stats" and line
        self.draw["full"].text(
            (34, 0), "Stats", font=self.FONTS["med_bold"], fill=self.COLOURS["white"]
        )
        self.draw["full"].line([(34, 10), (60, 10)], fill=self.COLOURS["white"])

        if self.team_stats:
            # Display stats - we need to get W-L-OTL from somewhere
            # For now, just show rank and points
            self.draw["full"].text(
                (34, 12),
                f"{self.team_stats['wins']}-{self.team_stats['losses']}-{self.team_stats['ot_losses']}",
                font=self.FONTS["sm"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].text(
                (34, 20),
                f"Rk:{self.team_stats['rank']}",
                font=self.FONTS["sm"],
                fill=self.COLOURS["white"],
            )

    def _draw_time(self, time_str, y_offset):
        if time_str[0] == "1":
            self.draw["full"].text(
                (35, y_offset),
                time_str[0],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].text(
                (41, y_offset),
                time_str[1],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].point((47, y_offset + 4), fill=self.COLOURS["white"])
            self.draw["full"].point((47, y_offset + 6), fill=self.COLOURS["white"])
            self.draw["full"].text(
                (49, y_offset),
                time_str[3],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].text(
                (55, y_offset),
                time_str[4],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
        else:
            self.draw["full"].text(
                (38, y_offset),
                time_str[1],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].point((44, y_offset + 4), fill=self.COLOURS["white"])
            self.draw["full"].point((44, y_offset + 6), fill=self.COLOURS["white"])
            self.draw["full"].text(
                (46, y_offset),
                time_str[3],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )
            self.draw["full"].text(
                (52, y_offset),
                time_str[4],
                font=self.FONTS["med"],
                fill=self.COLOURS["white"],
            )

    def _add_team_logo(self, team):
        logo_path = (
            self.app_dir / "resources" / "images" / "NHL" / "teams" / f"{team}.png"
        )
        if logo_path.exists():
            team_logo = Image.open(logo_path).convert("RGB")
            team_logo = crop_image(team_logo)
            team_logo.thumbnail((30, 30))

            row_location = math.floor(1 + (30 - team_logo.size[0]) / 2)
            col_location = math.ceil(1 + (30 - team_logo.size[1]) / 2)

            self.images["full"].paste(team_logo, (row_location, col_location))

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            return "menu"
        elif input_type in ["left", "right"]:
            self.show_stats = not self.show_stats
        return None
