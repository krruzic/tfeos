from pathlib import Path
from typing import Annotated, Any, Dict, List

from litestar import Request, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.enums import RequestEncodingType
from litestar.params import Body
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

    all_applications = [
        {"name": a.metadata["name"]} for a in manager.get_all_applications()
    ]

    return Template(
        template_name="app_config.html",
        context={
            "metadata": app.metadata,
            "dsl": app.dsl,
            "config": app.config,
            "all_applications": all_applications,
        },
    )


@post("/applications/{app_name:str}/config")
async def update_config(app_name: str, request: Request) -> Redirect:
    manager = request.app.state.app_manager
    app = manager.get_application(app_name)

    if not app:
        return Redirect(path="/")

    form_data = await request.form()
    data = dict(form_data)

    processed_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            processed_data[key] = value[-1]
        else:
            processed_data[key] = value

    for key, value in processed_data.items():
        if isinstance(value, str):
            if value.lower() == "true":
                processed_data[key] = True
            elif value.lower() == "false":
                processed_data[key] = False
            else:
                try:
                    processed_data[key] = int(value)
                except ValueError:
                    try:
                        processed_data[key] = float(value)
                    except ValueError:
                        pass

    from appkit.validation import ConfigValidator

    valid, errors = ConfigValidator.validate(processed_data, app.dsl)

    if valid:
        manager.update_config(app_name, processed_data)

    return Redirect(path=f"/applications/{app_name}/config")
