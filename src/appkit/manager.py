import importlib.util
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Application, ApplicationConfig

logger = logging.getLogger(__name__)


class ApplicationManager:
    def __init__(self, apps_dir: Path):
        self.apps_dir = apps_dir
        self.applications: Dict[str, Any] = {}

    def load_applications(self) -> None:
        for app_dir in self.apps_dir.iterdir():
            if app_dir.is_dir() and (app_dir / "metadata.json").exists():
                try:
                    app_config = ApplicationConfig(app_dir)
                    self.applications[app_config.metadata["name"]] = app_config
                except Exception as e:
                    logger.exception(
                        f"Failed to load application config from {app_dir}: {e}"
                    )

    def launch_application(self, app_name: str, matrix) -> Optional[Application]:
        app_config: Optional[ApplicationConfig] = self.get_application(app_name)
        if app_config:
            module_path = app_config.app_dir / "app.py"
            spec = importlib.util.spec_from_file_location("app", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.App(app_config, matrix)
        logger.error(f"Failed to launch application: {app_name}")
        return None

    def get_application(self, name: str) -> Optional[ApplicationConfig]:
        return self.applications.get(name)

    def get_all_applications(self) -> List[ApplicationConfig]:
        return list(self.applications.values())

    def update_config(self, app_name: str, config: Dict[str, Any]) -> None:
        app = self.get_application(app_name)
        if app:
            app.save_config(config)
