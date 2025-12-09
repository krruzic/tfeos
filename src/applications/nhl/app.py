from pathlib import Path
from typing import Optional

from tfeos.input import InputType, InputResult
from appkit.base import Application, Scene, ApplicationConfig
from appkit.config import Config
from applications.nhl.scenes.games import NHLGamesScene
from applications.nhl.scenes.favourite_team import NHLFavouriteTeamScene
from applications.nhl.scenes.standings import NHLStandingsScene


class App(Application):
    def __init__(self, application_config: ApplicationConfig, matrix):
        super().__init__(application_config, matrix)
        self.scenes = {
            "standings": NHLStandingsScene(self.application_config),
            "games": NHLGamesScene(self.application_config),
            "favourite": NHLFavouriteTeamScene(self.application_config),
        }
        if self.application_config.config.get("default_scene") == "Standings":
            self.scene = self.scenes["standings"]
            self.current_scene_index = 0
        if self.application_config.config.get("default_scene") == "Scores":
            self.scene = self.scenes["games"]
            self.current_scene_index = 1
        else:
            self.scene = self.scenes["favourite"]
            self.current_scene_index = 2
        self.scene_order = ["games", "standings", "favourite"]

    def get_framerate(self) -> int:
        return 10

    def handle_new_config(self, new_config: Config) -> None:
        return

    def _render(self, canvas) -> None:
        self.scene.render(canvas)

    def _handle_input(self, input_type: InputType) -> Optional[InputResult]:
        if input_type == InputType.UP:
            self.current_scene_index = (self.current_scene_index - 1) % len(
                self.scene_order
            )
            self.scene = self.scenes.get(self.scene_order[self.current_scene_index])
            return None
        elif input_type == InputType.DOWN:
            self.current_scene_index = (self.current_scene_index + 1) % len(
                self.scene_order
            )
            self.scene = self.scenes.get(self.scene_order[self.current_scene_index])
            return None
        self.scene.handle_input(input_type)


