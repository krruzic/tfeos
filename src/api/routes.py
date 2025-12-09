import logging
from pathlib import Path
from typing import Annotated, Any, Dict, List

from litestar import Request, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Redirect, Template

from appkit.base import ApplicationConfig
from appkit.config import Config
from appkit.manager import ApplicationManager
from appkit.validation import ConfigValidator

logger = logging.getLogger("tfeos.routes")


@get("/")
async def app_list(request: Request) -> Template:
    manager: ApplicationManager = request.app.state.app_manager
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
        template_name="app_list.html",
        context={"applications": applications, "show_sidebar": False},
    )


@get("/applications/{app_name:str}/config")
async def app_config_page(app_name: str, request: Request) -> Template:
    try:
        manager: ApplicationManager = request.app.state.app_manager
        app: Optional[ApplicationConfig] = manager.get_application(app_name)

        if not app:
            return Redirect(path="/")

        sidebar_apps = [
            {"name": a.metadata["name"], "icon": a.metadata.get("icon")}
            for a in manager.get_all_applications()
        ]

        return Template(
            template_name="app_config.html",
            context={
                "metadata": app.metadata,
                "dsl": app.dsl,
                "config": app.config,
                "show_sidebar": True,
                "sidebar_apps": sidebar_apps,
                "current_app": app_name,
            },
        )
    except Exception as e:
        logger.error(f"Error loading config page for {app_name}: {e}", exc_info=True)
        raise


@post("/applications/{app_name:str}/config")
async def update_config(app_name: str, request: Request) -> Redirect:
    manager: ApplicationManager = request.app.state.app_manager
    app = manager.get_application(app_name)

    if not app:
        return Redirect(path="/")

    form_data = await request.form()

    processed_data = {}
    for key, value in form_data.items():
        if key.endswith("[]"):
            actual_key = key[:-2]
            if isinstance(value, list):
                processed_data[actual_key] = [v for v in value if v.strip()]
            else:
                if processed_data.get(actual_key):
                    if value.strip():
                        processed_data[actual_key].append(value)
                else:
                    processed_data[actual_key] = [value] if value.strip() else []
        else:
            if isinstance(value, list):
                processed_data[key] = value[-1]
            else:
                processed_data[key] = value

    checkbox_fields = []
    if "settings" in app.dsl:
        checkbox_fields.extend(
            [s["name"] for s in app.dsl["settings"] if s["type"] == "checkbox"]
        )
    if "setting_groups" in app.dsl:
        for group in app.dsl["setting_groups"]:
            checkbox_fields.extend(
                [s["name"] for s in group["settings"] if s["type"] == "checkbox"]
            )

    for field in checkbox_fields:
        if field not in processed_data:
            processed_data[field] = False

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

    valid, errors = ConfigValidator.validate(processed_data, app.dsl)

    if valid:
        os_instance = request.app.state.os_instance
        manager.update_config(app_name, processed_data)
        os_instance.on_app_config_changed(app_name, Config(processed_data))

    return Redirect(path=f"/applications/{app_name}/config")
