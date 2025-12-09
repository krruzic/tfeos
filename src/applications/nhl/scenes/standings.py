import math
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from tfeos.input import InputType, InputResult
from appkit.base import Scene
from appkit.graphics_helpers import MatrixCanvas, Region

from .nhl_api import get_standings


class NHLStandingsScene(Scene):
    def __init__(self, application_config):
        self.config = application_config.config
        self.app_dir = application_config.app_dir
        self.data = {}
        self.current_view_type = None
        self.current_division_index = 0
        self.current_conference_index = 0
        self.last_update = None
        self.scroll_offset = 0
        self.last_scroll_time = time.time()
        self.scroll_pause_until = time.time() + 0.5
        self.scroll_at_bottom = False

        self.divisions = ["Atlantic", "Metropolitan", "Central", "Pacific"]
        self.conferences = ["Eastern", "Western"]

        self.matrix_canvas = MatrixCanvas()
        
        self.side_region = Image.new("RGB", (8, 32))
        self.standings_region = Image.new("RGB", (56, 256))
        self.side_draw = ImageDraw.Draw(self.side_region)
        self.standings_draw = ImageDraw.Draw(self.standings_region)

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

        self._initialize_view()

    def _initialize_view(self):
        default_view = self.config.get("default_view", "Conference")
        default_division = self.config.get("default_division", "Atlantic")
        default_conference = self.config.get("default_conference", "Eastern")

        self.current_view_type = default_view

        if default_division in self.divisions:
            self.current_division_index = self.divisions.index(default_division)

        if default_conference in self.conferences:
            self.current_conference_index = self.conferences.index(default_conference)

    def render(self, canvas) -> None:
        if not self.last_update or (datetime.now() - self.last_update).seconds > 300:
            self.data["standings"] = get_standings()
            self.last_update = datetime.now()

        if not self.data.get("standings"):
            self.matrix_canvas.clear_region(Region.FULL)
            self.matrix_canvas.draw_text(
                Region.FULL, 2, 12, "Loading...", self.colours["white"], self.fonts["sm"]
            )
            self.matrix_canvas.render_frame(canvas)
            return

        view_data = self._get_current_view_data()
        if not view_data:
            return

        self._build_standings_image(view_data["name"], view_data["teams"])

        num_teams = len(view_data["teams"])
        max_scroll = max(0, (num_teams - 4) * 8)

        if max_scroll > 0:
            current_time = time.time()

            if self.scroll_at_bottom:
                if current_time >= self.scroll_pause_until:
                    self.scroll_offset = 0
                    self.scroll_at_bottom = False
                    self.last_scroll_time = current_time
            elif current_time < self.scroll_pause_until:
                pass
            elif current_time - self.last_scroll_time > 0.075:
                self.scroll_offset += 1
                self.last_scroll_time = current_time

                if self.scroll_offset >= max_scroll:
                    self.scroll_offset = max_scroll
                    self.scroll_pause_until = current_time + 1.0
                    self.scroll_at_bottom = True
                elif self.scroll_offset % 8 == 0:
                    self.scroll_pause_until = current_time + 1.0

        self.matrix_canvas.clear_region(Region.FULL)
        self.matrix_canvas.draw_image(Region.FULL, 0, 0, self.side_region)
        cropped_standings = self.standings_region.crop((0, self.scroll_offset, 56, self.scroll_offset + 32))
        self.matrix_canvas.draw_image(Region.FULL, 8, 0, cropped_standings)

        self.matrix_canvas.render_frame(canvas)

    def _get_current_view_data(self):
        standings = self.data["standings"]

        if self.current_view_type == "Division":
            division = self.divisions[self.current_division_index]
            div_data = standings["division"]["divisions"][division]
            return {"name": div_data["abrv"], "teams": div_data["teams"]}
        elif self.current_view_type == "Conference":
            conference = self.conferences[self.current_conference_index]
            conf_data = standings["conference"]["conferences"][conference]
            return {"name": conf_data["abrv"], "teams": conf_data["teams"]}
        else:
            league_data = standings["league"]["leagues"]["NHL"]
            return {"name": league_data["abrv"], "teams": league_data["teams"]}

    def _build_standings_image(self, name, teams):
        self.side_draw.rectangle([(0, 0), (8, 32)], fill=(0, 0, 0))
        self.standings_draw.rectangle([(0, 0), (56, 256)], fill=(0, 0, 0))

        tmp_img = Image.new("RGB", (32, 8))
        tmp_draw = ImageDraw.Draw(tmp_img)
        tmp_draw.rectangle([(0, 0), (32, 8)], fill=self.colours["white"])
        tmp_draw.text((1, 0), "NHL", font=self.fonts["sm"], fill=self.colours["black"])
        tmp_draw.text((17, 0), name, font=self.fonts["sm"], fill=self.colours["black"])
        tmp_img = tmp_img.rotate(90, expand=True)
        self.side_region.paste(tmp_img, (0, 0))

        fav_team = self.config.get("favourite_team")

        for row, team in enumerate(teams):
            y_offset = row * 8

            team_colour = (
                self.colours["yellow"]
                if team["team_abrv"] == fav_team
                else self.colours["white"]
            )

            if row < len(teams) - 1:
                self.standings_draw.line(
                    [(1, y_offset + 7), (54, y_offset + 7)],
                    fill=self.colours["grey_dark"],
                )

            rank_str = str(team["rank"])
            rank_offset = 5 if len(rank_str) < 2 else 0
            self.standings_draw.text(
                (1 + rank_offset, y_offset - 1),
                rank_str,
                font=self.fonts["sm"],
                fill=team_colour,
            )

            if team.get("has_clinched"):
                self.standings_draw.text(
                    (14, y_offset - 2),
                    "*",
                    font=self.fonts["med"],
                    fill=self.colours["red"],
                )

            self.standings_draw.text(
                (21, y_offset - 1),
                team["team_abrv"],
                font=self.fonts["sm"],
                fill=team_colour,
            )

            pts_str = str(team["points"])
            if team["points"] < 10:
                pts_offset = 0
            elif team["points"] < 100:
                pts_offset = -5
            else:
                pts_offset = -10
            self.standings_draw.text(
                (51 + pts_offset, y_offset - 1),
                pts_str,
                font=self.fonts["sm"],
                fill=team_colour,
            )

    def _reset_scroll(self):
        self.scroll_offset = 0
        self.scroll_pause_until = time.time() + 0.5
        self.scroll_at_bottom = False

    def handle_input(self, input_type: InputType):
        if input_type == InputType.ACCEPT:
            if self.current_view_type == "Division":
                self.current_view_type = "Conference"
            elif self.current_view_type == "Conference":
                self.current_view_type = "League"
            else:
                self.current_view_type = "Division"
            self._reset_scroll()
        elif input_type == InputType.RIGHT:
            if self.current_view_type == "Division":
                self.current_division_index = (self.current_division_index + 1) % len(
                    self.divisions
                )
                self._reset_scroll()
            elif self.current_view_type == "Conference":
                self.current_conference_index = (
                    self.current_conference_index + 1
                ) % len(self.conferences)
                self._reset_scroll()
        elif input_type == InputType.LEFT:
            if self.current_view_type == "Division":
                self.current_division_index = (self.current_division_index - 1) % len(
                    self.divisions
                )
                self._reset_scroll()
            elif self.current_view_type == "Conference":
                self.current_conference_index = (
                    self.current_conference_index - 1
                ) % len(self.conferences)
                self._reset_scroll()
        return None
