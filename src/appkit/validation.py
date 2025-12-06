# appkit/validation.py
from typing import Any, Dict, List, Tuple


class ConfigValidator:
    @staticmethod
    def validate(
        config_data: Dict[str, Any], dsl: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        errors = []

        settings = []
        if "settings" in dsl:
            settings.extend(dsl["settings"])
        if "setting_groups" in dsl:
            for group in dsl["setting_groups"]:
                settings.extend(group["settings"])

        for setting in settings:
            name = setting["name"]
            setting_type = setting["type"]

            if name not in config_data:
                errors.append(f"Missing required setting: {name}")
                continue

            value = config_data[name]

            if setting_type in ["dropdown", "radio"]:
                if value not in setting["options"]:
                    errors.append(f"Invalid value for {name}: {value} not in options")

            elif setting_type == "slider":
                try:
                    num_value = float(value)
                    if num_value < setting["min"] or num_value > setting["max"]:
                        errors.append(f"Value for {name} out of range: {num_value}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {name}: {value}")

            elif setting_type == "checkbox":
                if not isinstance(value, bool):
                    errors.append(f"Invalid boolean value for {name}: {value}")

            elif setting_type == "text":
                if not isinstance(value, str):
                    errors.append(f"Invalid text value for {name}: {value}")

            elif setting_type == "color":
                if not isinstance(value, str):
                    errors.append(f"Invalid color value for {name}: {value}")
                elif not value.startswith("#") or len(value) != 7:
                    errors.append(f"Invalid color format for {name}: {value}")

            elif setting_type == "list":
                if not isinstance(value, list):
                    errors.append(f"Invalid list value for {name}: {value}")

        return len(errors) == 0, errors


class DSLValidator:
    VALID_TYPES = ["dropdown", "text", "checkbox", "radio", "slider", "color", "list"]

    @staticmethod
    def validate(dsl: Dict[str, Any]) -> List[str]:
        errors = []

        if "settings" in dsl:
            for setting in dsl["settings"]:
                errors.extend(DSLValidator._validate_setting(setting))

        if "setting_groups" in dsl:
            for group in dsl["setting_groups"]:
                if "name" not in group:
                    errors.append("Setting group missing name")
                if "settings" not in group:
                    errors.append(
                        f"Setting group {group.get('name', 'unknown')} missing settings"
                    )
                else:
                    for setting in group["settings"]:
                        errors.extend(DSLValidator._validate_setting(setting))

        return errors

    @staticmethod
    def _validate_setting(setting: Dict[str, Any]) -> List[str]:
        errors = []

        if "name" not in setting:
            errors.append("Setting missing name")
        if "label" not in setting:
            errors.append(f"Setting {setting.get('name', 'unknown')} missing label")
        if "type" not in setting:
            errors.append(f"Setting {setting.get('name', 'unknown')} missing type")
        elif setting["type"] not in DSLValidator.VALID_TYPES:
            errors.append(
                f"Setting {setting.get('name', 'unknown')} has invalid type: {setting['type']}"
            )

        setting_type = setting.get("type")

        if setting_type in ["dropdown", "select", "radio"]:
            if "options" not in setting:
                errors.append(
                    f"Setting {setting.get('name', 'unknown')} missing options"
                )

        if setting_type == "slider":
            if "min" not in setting:
                errors.append(f"Setting {setting.get('name', 'unknown')} missing min")
            if "max" not in setting:
                errors.append(f"Setting {setting.get('name', 'unknown')} missing max")

        return errors
