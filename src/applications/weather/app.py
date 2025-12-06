import time
from pathlib import Path
from threading import Lock, Thread
from typing import Optional

import requests

from appkit.base import Application, Scene
from appkit.config import Config
from appkit.graphics_helpers import Color, Font, draw_text


class WeatherData:
    def __init__(self):
        self.data = {}
        self.lock = Lock()
        self.last_update = 0

    def update_weather(self, location: str, use_fahrenheit: bool):
        try:
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
            geo_response = requests.get(geocode_url, timeout=5)
            geo_data = geo_response.json()

            if "results" not in geo_data or len(geo_data["results"]) == 0:
                return

            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]

            temp_unit = "fahrenheit" if use_fahrenheit else "celsius"
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&temperature_unit={temp_unit}"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()

            if "current" in weather_data:
                temp = weather_data["current"]["temperature_2m"]
                weather_code = weather_data["current"]["weather_code"]
                condition = self._get_condition(weather_code)

                with self.lock:
                    self.data = {
                        "temp": temp,
                        "condition": condition,
                        "unit": "F" if use_fahrenheit else "C",
                    }
                    self.last_update = time.time()
        except Exception as e:
            print(f"Error updating weather: {e}")

    def _get_condition(self, code: int) -> str:
        if code == 0:
            return "Clear"
        elif code in [1, 2, 3]:
            return "Cloudy"
        elif code in [45, 48]:
            return "Fog"
        elif code in [51, 53, 55, 56, 57]:
            return "Drizzle"
        elif code in [61, 63, 65, 66, 67]:
            return "Rain"
        elif code in [71, 73, 75, 77]:
            return "Snow"
        elif code in [80, 81, 82]:
            return "Showers"
        elif code in [85, 86]:
            return "Snow"
        elif code in [95, 96, 99]:
            return "Thunder"
        else:
            return "Unknown"

    def get_weather(self):
        with self.lock:
            return self.data.copy() if self.data else None


class WeatherScene(Scene):
    def __init__(self, config, app_dir: Path):
        self.config = config
        self.app_dir = app_dir
        font_path = app_dir / "resources" / "7x13.bdf"
        self.font = Font(str(font_path))
        self.weather_data = WeatherData()
        self.update_thread = None
        self.running = True

        self.start_updates()

    def start_updates(self):
        self.update_thread = Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def update_now(self, new_config: Optional[Config] = None):
        Thread(target=self._do_update, args=(new_config,), daemon=True).start()

    def _do_update(self, new_config: Optional[Config] = None):
        if new_config:
            self.config = new_config
        location = self.config.get("location", "New York")
        use_fahrenheit = (
            self.config.get("temperature_unit", "Fahrenheit") == "Fahrenheit"
        )
        self.weather_data.update_weather(location, use_fahrenheit)

    def _update_loop(self):
        self._do_update()
        while self.running:
            time.sleep(3600)
            self._do_update()

    def render(self, canvas) -> None:
        canvas.Clear()

        draw_text(canvas, self.font, 2, 16, Color(255, 255, 0), "Loading...")
        data = self.weather_data.get_weather()
        canvas.Clear()

        if data:
            temp = data["temp"]
            condition = data["condition"]
            unit = data["unit"]

            temp_str = f"{temp:.0f}{unit}"

            draw_text(canvas, self.font, 2, 12, Color(255, 255, 255), temp_str)
            draw_text(canvas, self.font, 2, 24, Color(200, 200, 200), condition)
        else:
            draw_text(canvas, self.font, 2, 16, Color(255, 255, 0), "No data")

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            self.running = False
            return "menu"
        return None


class App(Application):
    def __init__(self, app_dir: Path):
        super().__init__(app_dir)
        self.scene = WeatherScene(self.config, self.app_dir)

    def on_config_changed(self, new_config: Config) -> None:
        self.scene.update_now(new_config)

    def get_framerate(self) -> int:
        return 10

    def get_scenes(self):
        return {"weather": WeatherScene(self.config, self.app_dir)}

    def default_scene(self) -> Scene:
        return WeatherScene(self.config, self.app_dir)

    def get_active_scene(self) -> Scene:
        return self.scene
