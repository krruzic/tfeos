import argparse
import logging
import select
import signal
import sys
import termios
import time
import tty
from pathlib import Path
from threading import Lock, Thread
from typing import Optional, final

import uvicorn

from api.app import create_app
from appkit.config import Config
from appkit.manager import Application, ApplicationManager
from appkit.menu import AppMenuItem, AppMenuScene

from .input import InputResult, InputType
from .logging import LOG_FORMAT

CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parent.parent
APPS_DIR = SRC_DIR / "applications"
TEMPLATES_DIR = SRC_DIR / "api" / "templates"

logger = logging.getLogger("tfeos")


@final
class LEDMatrixOS:
    def __init__(self, enable_input: bool, apps_dir: Path, enable_matrix: bool = True):
        self.apps_dir = apps_dir
        self.enable_matrix = enable_matrix
        self.running = False
        self.matrix = None
        self.canvas = None
        self.input_handler = None
        self.enable_input = enable_input
        self.manager = ApplicationManager(apps_dir)
        self.manager.load_applications()
        self.current_framerate = 30

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
        self.active_app: Optional[Application] = None

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
            logger.info("Matrix initialized")
        except ImportError:
            try:
                from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

                options = RGBMatrixOptions()
                options.rows = 32
                options.cols = 64
                options.chain_length = 1
                options.parallel = 1

                self.matrix = RGBMatrix(options=options)
                self.canvas = self.matrix.CreateFrameCanvas()
                logger.info("Using RGBMatrixEmulator")
            except ImportError:
                logger.warning(
                    "Neither rgbmatrix nor RGBMatrixEmulator found, matrix disabled"
                )
                self.enable_matrix = False
        except Exception as e:
            logger.error(f"Could not initialize matrix: {e}")
            self.enable_matrix = False

    def on_app_config_changed(self, app_name: str, new_config: Config):
        logger.info(f"Config changed for active app: {app_name}")
        if self.active_app:
            if self.active_app.application_config.app_name == app_name:
                self.active_app.handle_new_config(new_config)

    def read_input(self) -> Optional[InputType]:
        """Read input if available, returning InputType or None. Non-blocking"""

        if select.select([sys.stdin], [], [], 0)[0]:
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                ch = sys.stdin.read(1)

                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return InputType.UP
                        if ch3 == "B":
                            return InputType.DOWN
                        if ch3 == "C":
                            return InputType.RIGHT
                        if ch3 == "D":
                            return InputType.LEFT
                elif ch.lower() == "k":
                    return InputType.ACCEPT
                elif ch.lower() == "j":
                    return InputType.CANCEL
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        return None

    def core_loop(self):
        tty.setcbreak(sys.stdin.fileno())

        while self.running:
            input_key = self.read_input()

            if self.active_app:
                if input_key:
                    input_result = self.active_app.handle_input(input_key)
                    if input_result:
                        self.return_to_menu()
                        self.canvas.Clear()
                        continue
                self.active_app.render(self.canvas)
                sleep_time = 1.0 / self.active_app.get_framerate()
            else:
                if input_key:
                    input_result = self.menu_scene.handle_input(input_key)
                    if input_result:
                        self.handle_menu_selection(input_result)
                        self.canvas.Clear()
                        continue
                self.menu_scene.render(self.canvas)
                sleep_time = 1.0 / self.current_framerate
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            time.sleep(sleep_time)

    def handle_menu_selection(self, app_name: str):
        app = self.manager.launch_application(app_name, self.matrix)
        if app:
            self.active_app = app
            logger.info(f"Launched app: {app_name}")

    def return_to_menu(self):
        self.active_app = None
        self.current_framerate = 30
        logger.info("Returned to menu")

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        logger.info(f"Loaded {len(self.manager.get_all_applications())} applications")

        self.setup_matrix()
        self.running = True

        app = create_app(
            self.apps_dir,
            TEMPLATES_DIR,
            {"app_manager": self.manager, "os_instance": self},
        )

        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["access"]["fmt"] = LOG_FORMAT
        log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
        config = uvicorn.Config(app, host=host, port=port, log_config=log_config)
        server = uvicorn.Server(config)

        # Run uvicorn in a thread instead of main thread
        api_thread = Thread(target=server.run, daemon=True, name="APIThread")
        api_thread.start()

        def signal_handler(sig, frame):
            logger.info("Shutting down...")
            self.running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info(f"API server running at http://{host}:{port}")
        if self.enable_input:
            logger.info("Controls: Arrow keys to navigate, K to accept, J to cancel")

        # Keep main thread alive
        try:
            self.core_loop()
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)

def main():
    parser = argparse.ArgumentParser(description="Twenty Forty Eight OS")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--no-matrix", action="store_true", help="Disable LED matrix")
    parser.add_argument(
        "--no-input", action="store_true", help="Disable keyboard input"
    )
    parser.add_argument(
        "--apps-dir", type=Path, default=APPS_DIR, help="Applications directory"
    )

    args = parser.parse_args()

    enable_input = not args.no_input

    os_instance = LEDMatrixOS(
        enable_input, args.apps_dir, enable_matrix=not args.no_matrix
    )
    os_instance.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
