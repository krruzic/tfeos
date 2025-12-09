from pathlib import Path
from typing import Dict, Any
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.template.config import TemplateConfig

from appkit.manager import ApplicationManager

from .routes import app_config_page, app_list, update_config


async def after_exception_handler(
    exc: Exception, scope: "Scope", state: "State"
) -> None:
    raise Exception


def create_app(apps_dir: Path, templates_dir: Path, state: Dict[str, Any]) -> Litestar:
    app = Litestar(
        after_exception=[after_exception_handler],
        route_handlers=[app_list, app_config_page, update_config],
        template_config=TemplateConfig(
            directory=templates_dir, engine=JinjaTemplateEngine
        ),
        state=State(state),
    )

    return app
