import sys
import termios
import time
import tty
from threading import Lock, Thread
from typing import Callable, Optional


class InputHandler:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.running = False
        self.thread = None
        self.cancel_held = False
        self.cancel_start_time = None
        self.lock = Lock()

    def start(self):
        self.running = True
        self.thread = Thread(target=self._input_loop, daemon=True)
        self.thread.start()
        self.hold_check_thread = Thread(target=self._hold_check_loop, daemon=True)
        self.hold_check_thread.start()

    def stop(self):
        self.running = False

    def _hold_check_loop(self):
        while self.running:
            with self.lock:
                if self.cancel_held and self.cancel_start_time:
                    elapsed = time.time() - self.cancel_start_time
                    if elapsed >= 3.0:
                        self.callback("force_exit")
                        self.cancel_held = False
                        self.cancel_start_time = None
            time.sleep(0.1)

    def _input_loop(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)

            while self.running:
                ch = sys.stdin.read(1)

                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            self.callback("up")
                        elif ch3 == "B":
                            self.callback("down")
                        elif ch3 == "C":
                            self.callback("right")
                        elif ch3 == "D":
                            self.callback("left")
                elif ch == "k":
                    self.callback("accept")
                elif ch == "j":
                    with self.lock:
                        if not self.cancel_held:
                            self.cancel_held = True
                            self.cancel_start_time = time.time()
                            self.callback("cancel")
                elif ch == "\x03":
                    break
                else:
                    with self.lock:
                        if self.cancel_held:
                            self.cancel_held = False
                            self.cancel_start_time = None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
