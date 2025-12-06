import math
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from appkit.base import Scene
from appkit.graphics_helpers import clear_image, set_image_on_canvas

from .nhl_api import get_standings


class NHLStandingsScene(Scene):
    def __init__(self, config, app_dir: Path):
        super().__init__()
        self.config = config
        self.app_dir = app_dir
        self.data = {}
        self.current_view_type = None  # 'Division', 'Conference', or 'League'
        self.current_division_index = 0
        self.current_conference_index = 0
        self.last_update = None
        self.scroll_offset = 0
        self.last_scroll_time = time.time()
        self.scroll_pause_until = time.time() + 0.5  # Initial pause before scrolling
        self.scroll_at_bottom = False

        self.divisions = ["Atlantic", "Metropolitan", "Central", "Pacific"]
        self.conferences = ["Eastern", "Western"]

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
        self.images = {
            "side": Image.new("RGB", (8, 32)),
            "standings": Image.new("RGB", (56, 256)),
            "full": Image.new("RGB", (64, 32)),
        }

        self.draw = {
            "side": ImageDraw.Draw(self.images["side"]),
            "standings": ImageDraw.Draw(self.images["standings"]),
            "full": ImageDraw.Draw(self.images["full"]),
        }

        self.LEAGUE = "NHL"
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
        # Update standings data every 5 minutes
        if not self.last_update or (datetime.now() - self.last_update).seconds > 300:
            self.data["standings"] = get_standings()
            self.last_update = datetime.now()

        if not self.data.get("standings"):
            clear_image(self.images["full"], self.draw["full"])
            self.draw["full"].text(
                (2, 12), "Loading...", font=self.FONTS["sm"], fill=self.COLOURS["white"]
            )
            set_image_on_canvas(canvas, self.images["full"])
            return

        # Get current view data
        view_data = self._get_current_view_data()
        if not view_data:
            return

        # Build standings for current view
        self._build_standings_image(view_data["name"], view_data["teams"])

        # Handle scrolling
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
                # Paused at a row
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

        # Compose and display
        clear_image(self.images["full"], self.draw["full"])
        self.images["full"].paste(self.images["side"], (0, 0))
        self.images["full"].paste(self.images["standings"], (8, -self.scroll_offset))

        set_image_on_canvas(canvas, self.images["full"])

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
        else:  # League
            league_data = standings["league"]["leagues"]["NHL"]
            return {"name": league_data["abrv"], "teams": league_data["teams"]}

    def _build_standings_image(self, name, teams):
        # Clear images
        clear_image(self.images["side"], self.draw["side"])
        clear_image(self.images["standings"], self.draw["standings"])

        # Build sidebar
        tmp_img = Image.new("RGB", (32, 8))
        tmp_draw = ImageDraw.Draw(tmp_img)
        tmp_draw.rectangle([(0, 0), (32, 8)], fill=self.COLOURS["white"])
        tmp_draw.text(
            (1, 0), self.LEAGUE, font=self.FONTS["sm"], fill=self.COLOURS["black"]
        )
        tmp_draw.text((17, 0), name, font=self.FONTS["sm"], fill=self.COLOURS["black"])
        tmp_img = tmp_img.rotate(90, expand=True)
        self.images["side"].paste(tmp_img, (0, 0))

        # Build standings rows
        fav_team = self.config.get("favourite_team")

        for row, team in enumerate(teams):
            y_offset = row * 8

            # Determine team color
            team_colour = (
                self.COLOURS["yellow"]
                if team["team_abrv"] == fav_team
                else self.COLOURS["white"]
            )

            # Draw horizontal line
            if row < len(teams) - 1:
                self.draw["standings"].line(
                    [(1, y_offset + 7), (54, y_offset + 7)],
                    fill=self.COLOURS["grey_dark"],
                )

            # Draw rank
            rank_str = str(team["rank"])
            rank_offset = 5 if len(rank_str) < 2 else 0
            self.draw["standings"].text(
                (1 + rank_offset, y_offset - 1),
                rank_str,
                font=self.FONTS["sm"],
                fill=team_colour,
            )

            # Draw clinch indicator
            if team.get("has_clinched"):
                self.draw["standings"].text(
                    (14, y_offset - 2),
                    "*",
                    font=self.FONTS["med"],
                    fill=self.COLOURS["red"],
                )

            # Draw team abbreviation
            self.draw["standings"].text(
                (21, y_offset - 1),
                team["team_abrv"],
                font=self.FONTS["sm"],
                fill=team_colour,
            )

            # Draw points
            pts_str = str(team["points"])
            if team["points"] < 10:
                pts_offset = 0
            elif team["points"] < 100:
                pts_offset = -5
            else:
                pts_offset = -10
            self.draw["standings"].text(
                (51 + pts_offset, y_offset - 1),
                pts_str,
                font=self.FONTS["sm"],
                fill=team_colour,
            )

    def _reset_scroll(self):
        self.scroll_offset = 0
        self.scroll_pause_until = time.time() + 0.5
        self.scroll_at_bottom = False

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            return "menu"
        elif input_type == "accept":
            # Cycle through view types: Division -> Conference -> League -> Division
            if self.current_view_type == "Division":
                self.current_view_type = "Conference"
            elif self.current_view_type == "Conference":
                self.current_view_type = "League"
            else:
                self.current_view_type = "Division"
            self._reset_scroll()
        elif input_type == "right":
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
        elif input_type == "left":
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
