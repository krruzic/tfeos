import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config


class Scene(ABC):
    @abstractmethod
    def render(self, canvas) -> None:
        pass

    @abstractmethod
    def handle_input(self, input_type: str) -> Optional[str]:
        """Handle input and return next scene name if scene should change"""
        pass


class Application(ABC):
    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.metadata = self._load_metadata()
        self.dsl = self._load_dsl()
        self.config = self._load_config()

    def get_framerate(self) -> int:
        """Return desired framerate for this app. Default is 30 FPS."""
        return 30

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

    @abstractmethod
    def on_config_changed(self, config: Config):
        """Notify on config change"""
        pass

    @abstractmethod
    def get_scenes(self) -> Dict[str, Scene]:
        pass

    @abstractmethod
    def default_scene(self) -> Scene:
        """Return default scene for this application, shown at startup"""
        pass

    @abstractmethod
    def get_active_scene(self) -> Scene:
        """Return active scene for this application"""
        pass

    def get_icon_data(self) -> Optional[bytes]:
        """Get decoded icon bytes from base64"""
        import base64

        icon_b64 = self.metadata.get("icon")
        if icon_b64:
            return base64.b64decode(icon_b64)
        return None
