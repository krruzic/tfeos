from pathlib import Path

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.template.config import TemplateConfig

from appkit.manager import ApplicationManager

from .routes import app_config_page, app_list, update_config


def create_app(apps_dir: Path, templates_dir: Path) -> Litestar:
    manager = ApplicationManager(apps_dir)
    manager.load_applications()

    app = Litestar(
        route_handlers=[app_list, app_config_page, update_config],
        template_config=TemplateConfig(
            directory=templates_dir, engine=JinjaTemplateEngine
        ),
        state=State({"app_manager": manager}),
    )

    return app
