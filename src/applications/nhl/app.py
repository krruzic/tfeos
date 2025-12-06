from pathlib import Path
from typing import Optional

from appkit.base import Application, Scene
from appkit.config import Config
from applications.nhl.scenes.games import NHLGamesScene
from applications.nhl.scenes.next_game import NHLNextGameScene
from applications.nhl.scenes.standings import NHLStandingsScene


class App(Application):
    def __init__(self, app_dir: Path):
        super().__init__(app_dir)
        self.scene = self.default_scene()
        self.scene_order = ["games", "standings", "next_game"]
        self.current_scene_index = 0

    def get_framerate(self) -> int:
        return 10

    def get_scenes(self):
        return {
            "games": NHLGamesScene(self.config, self.app_dir),
            "standings": NHLStandingsScene(self.config, self.app_dir),
            "next_game": NHLNextGameScene(self.config, self.app_dir),
        }

    def on_config_changed(self, new_config: Config) -> None:
        return

    def get_framerate(self) -> int:
        return 10

    def default_scene(self) -> Scene:
        if self.config.get("default_scene") == "Standings":
            return NHLStandingsScene(self.config, self.app_dir)
        if self.config.get("default_scene") == "Scores":
            return NHLGamesScene(self.config, self.app_dir)
        else:
            return NHLNextGameScene(self.config, self.app_dir)

    def get_active_scene(self) -> Scene:
        return self.scene

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "up":
            self.current_scene_index = (self.current_scene_index - 1) % len(
                self.scene_order
            )
            return self.scene_order[self.current_scene_index]
        elif input_type == "down":
            self.current_scene_index = (self.current_scene_index + 1) % len(
                self.scene_order
            )
            return self.scene_order[self.current_scene_index]
        return None
