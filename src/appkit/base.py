import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from tfeos.input import InputResult, InputType

from .config import Config


class ApplicationConfig:
    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.metadata = self._load_metadata()
        self.dsl = self._load_dsl()
        self.config = self._load_config()
        self.app_name: str = self.metadata["name"]

    def _load_metadata(self) -> Dict[str, Any]:
        with open(self.app_dir / "metadata.json") as f:
            return json.load(f)

    def _load_dsl(self) -> Dict[str, Any]:
        with open(self.app_dir / "dsl.json") as f:
            return json.load(f)

    def _load_config(self) -> Config:
        config_path = self.app_dir / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return Config(json.load(f))
        return Config(self._generate_default_config())

    def _generate_default_config(self) -> Dict[str, Any]:
        config = {}
        if "settings" in self.dsl:
            for setting in self.dsl["settings"]:
                config[setting["name"]] = setting.get("default")
        if "setting_groups" in self.dsl:
            for group in self.dsl["setting_groups"]:
                for setting in group["settings"]:
                    config[setting["name"]] = setting.get("default")
        return config

    def save_config(self, config_data: Dict[str, Any]):
        self.config = Config(config_data)
        with open(self.app_dir / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    def get_icon_data(self) -> Optional[bytes]:
        """Get decoded icon bytes from base64"""
        import base64

        icon_b64 = self.metadata.get("icon")
        if icon_b64:
            return base64.b64decode(icon_b64)
        return None


class Scene(ABC):
    def __init__(self, matrix):
        self.matrix = matrix


class Application(ABC):
    def __init__(self, application_config: ApplicationConfig, matrix):
        self.application_config = application_config
        self.matrix = matrix

    def cleanup(self):
        return

    def get_framerate(self) -> int:
        """Return desired framerate for this app. Default is 30 FPS."""
        return 30

    def render(self, canvas) -> Image.Image:
        canvas.Clear()
        return self._render(canvas)

    @abstractmethod
    def _render(self, canvas) -> None:
        pass

    def handle_input(self, input_type: InputType) -> Optional[InputResult]:
        if input_type == InputType.CANCEL:
            self.cleanup()
            return InputResult.MENU
        return self._handle_input(input_type)

    @abstractmethod
    def _handle_input(self, input_type: InputType) -> Optional[InputResult]:
        """Handle input at app level. Pass to scene or handle directly for single scene apps"""
        pass

    @abstractmethod
    def handle_new_config(self, config: Config):
        """Handle a new config being loaded"""
        pass

