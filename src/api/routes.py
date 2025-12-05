from pathlib import Path
from typing import Any, Dict, List

from litestar import Request, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.response import Redirect, Template


@get("/")
async def app_list(request: Request) -> Template:
    manager = request.app.state.app_manager
    applications = [
        {
            "name": app.metadata["name"],
            "version": app.metadata["version"],
            "icon": app.metadata.get("icon"),
            "description": app.metadata["description"],
            "author": app.metadata["author"],
        }
        for app in manager.get_all_applications()
    ]

    return Template(
        template_name="app_list.html", context={"applications": applications}
    )


@get("/applications")
async def list_applications(state: State) -> List[Dict[str, Any]]:
    manager: ApplicationManager = state.app_manager
    return [
        {
            "name": app.metadata["name"],
            "version": app.metadata["version"],
            "icon": app.metadata["icon"],
            "description": app.metadata["description"],
            "author": app.metadata["author"],
        }
        for app in manager.get_all_applications()
    ]


@get("/applications/{app_name:str}")
async def get_application_details(app_name: str, state: State) -> Dict[str, Any]:
    manager: ApplicationManager = state.app_manager
    app = manager.get_application(app_name)
    if not app:
        return {"error": "Application not found"}

    return {"metadata": app.metadata, "dsl": app.dsl, "config": app.config}


@get("/applications/{app_name:str}/config")
async def app_config_page(app_name: str, request: Request) -> Template:
    manager = request.app.state.app_manager
    app = manager.get_application(app_name)

    if not app:
        return Redirect(path="/")

    return Template(
        template_name="app_config.html",
        context={"metadata": app.metadata, "dsl": app.dsl, "config": app.config},
    )


@post("/applications/{app_name:str}/config")
async def update_config(
    app_name: str, data: Dict[str, Any], request: Request
) -> Redirect:
    manager = request.app.state.app_manager
    app = manager.get_application(app_name)

    if not app:
        return Redirect(path="/")

    from appkit.validation import ConfigValidator

    valid, errors = ConfigValidator.validate(data, app.dsl)

    if valid:
        manager.update_config(app_name, data)

    return Redirect(path=f"/applications/{app_name}/config")
