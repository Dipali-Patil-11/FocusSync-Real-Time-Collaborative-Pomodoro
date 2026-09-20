from enum import Enum

class TimerMode(str, Enum):
    FOCUS = "FOCUS"
    SHORT_BREAK = "SHORT_BREAK"
    LONG_BREAK = "LONG_BREAK"

class TimerStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

MAX_PARTICIPANTS = 5
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 60
