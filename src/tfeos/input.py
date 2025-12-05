import sys
import termios
import tty
from threading import Thread
from typing import Callable, Optional


class InputHandler:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = Thread(target=self._input_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _input_loop(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)

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
                    self.callback("cancel")
                elif ch == "\x03":
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
