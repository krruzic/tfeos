import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Application

logger = logging.getLogger(__name__)


class ApplicationManager:
    def __init__(self, apps_dir: Path):
        self.apps_dir = apps_dir
        self.applications: Dict[str, Any] = {}

    def load_applications(self) -> None:
        for app_dir in self.apps_dir.iterdir():
            if app_dir.is_dir() and (app_dir / "metadata.json").exists():
                try:
                    app = self._load_application(app_dir)
                    self.applications[app.metadata["name"]] = app
                except Exception as e:
                    logger.exception(f"Failed to load application from {app_dir}: {e}")

    def _load_application(self, app_dir: Path):
        import importlib.util

        module_path = app_dir / "app.py"
        spec = importlib.util.spec_from_file_location("app", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.App(app_dir)

    def get_application(self, name: str) -> Optional[Application]:
        return self.applications.get(name)

    def get_all_applications(self) -> List[Application]:
        return list(self.applications.values())

    def update_config(
        self, app_name: str, config: Dict[str, Any], notify_callback=None
    ) -> None:
        app = self.get_application(app_name)
        if app:
            app.save_config(config)
            if notify_callback:
                notify_callback(app_name)
