import sys
import termios
import tty
from enum import Enum
from threading import Thread
from typing import Callable, Optional


class InputType(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ACCEPT = "accept"
    CANCEL = "cancel"


class InputResult(str, Enum):
    MENU = "menu"
