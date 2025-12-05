import argparse
import signal
import sys
import time
from pathlib import Path
from threading import Thread

import uvicorn


def find_project_root() -> Path:
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


PROJECT_ROOT = find_project_root()
APPS_DIR = PROJECT_ROOT / "src" / "applications"
TEMPLATES_DIR = PROJECT_ROOT / "src" / "api" / "templates"


class LEDMatrixOS:
    def __init__(self, apps_dir: Path, enable_matrix: bool = True):
        self.apps_dir = apps_dir
        self.enable_matrix = enable_matrix
        self.running = False
        self.matrix = None
        self.canvas = None
        self.current_scene = None

        from appkit.manager import ApplicationManager
        from appkit.menu import AppMenuItem, AppMenuScene

        self.manager = ApplicationManager(apps_dir)
        self.manager.load_applications()

        menu_items = []
        for app in self.manager.get_all_applications():
            menu_items.append(
                AppMenuItem(
                    name=app.metadata["name"],
                    display_name=app.metadata["name"],
                    icon_data=app.get_icon_data(),
                )
            )

        self.menu_scene = AppMenuScene(menu_items)
        self.current_scene = self.menu_scene
        self.active_app = None

    def setup_matrix(self):
        if not self.enable_matrix:
            return

        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions

            options = RGBMatrixOptions()
            options.rows = 32
            options.cols = 64
            options.chain_length = 1
            options.parallel = 1
            options.hardware_mapping = "regular"

            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()
        except ImportError:
            try:
                from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

                print("Using RGBMatrixEmulator")

                options = RGBMatrixOptions()
                options.rows = 32
                options.cols = 64
                options.chain_length = 1
                options.parallel = 1

                self.matrix = RGBMatrix(options=options)
                self.canvas = self.matrix.CreateFrameCanvas()
            except ImportError:
                print(
                    "Warning: Neither rgbmatrix nor RGBMatrixEmulator found, matrix disabled"
                )
                self.enable_matrix = False
        except Exception as e:
            print(f"Warning: Could not initialize matrix: {e}")
            self.enable_matrix = False

    def render_loop(self):
        while self.running:
            if self.enable_matrix and self.canvas:
                self.canvas.Clear()

                if self.current_scene:
                    self.current_scene.render(self.canvas)

                self.canvas = self.matrix.SwapOnVSync(self.canvas)

            time.sleep(0.016)

    def handle_menu_selection(self, app_name: str):
        app = self.manager.get_application(app_name)
        if app:
            scene = app.get_active_scene()
            if scene:
                self.current_scene = scene
                self.active_app = app_name

    def return_to_menu(self):
        self.current_scene = self.menu_scene
        self.active_app = None

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        print(f"Loaded {len(self.manager.get_all_applications())} applications")

        self.setup_matrix()

        self.running = True

        render_thread = Thread(target=self.render_loop, daemon=True)
        render_thread.start()

        from api.app import create_app

        app = create_app(self.apps_dir, TEMPLATES_DIR)
        app.state.app_manager = self.manager
        app.state.os_instance = self

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        def signal_handler(sig, frame):
            print("\nShutting down...")
            self.running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"API server running at http://{host}:{port}")
        server.run()

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="Twenty Forty Eight OS")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--no-matrix", action="store_true", help="Disable LED matrix")
    parser.add_argument(
        "--apps-dir", type=Path, default=APPS_DIR, help="Applications directory"
    )

    args = parser.parse_args()

    if not args.apps_dir.exists():
        args.apps_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created applications directory: {args.apps_dir}")

    os_instance = LEDMatrixOS(args.apps_dir, enable_matrix=not args.no_matrix)
    os_instance.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
