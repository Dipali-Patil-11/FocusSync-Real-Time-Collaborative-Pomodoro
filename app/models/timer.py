from dataclasses import dataclass, field
import time
from app.utilities.constants import TimerMode, TimerStatus

@dataclass
class TimerState:
    session_code: str
    mode: str = TimerMode.FOCUS.value
    status: str = TimerStatus.IDLE.value
    duration: int = 1500  # 25 minutes in seconds
    remaining_seconds: int = 1500
    started_at: float = None  # Unix timestamp in seconds
    target_end_time: float = None  # Unix timestamp in seconds
    completed_sessions: int = 0
    total_focus_sessions: int = 0
    total_completed_cycles: int = 0
    total_focus_time_seconds: int = 0
    updated_at: float = field(default_factory=lambda: time.time())

    def calculate_current_remaining(self) -> int:
        """Calculate remaining seconds based on server current timestamp."""
        if self.status != TimerStatus.RUNNING.value:
            return max(0, int(self.remaining_seconds))
        
        now = time.time()
        if self.target_end_time:
            remaining = int(self.target_end_time - now)
            return max(0, remaining)
        return max(0, int(self.remaining_seconds))

    def to_dict(self):
        current_rem = self.calculate_current_remaining()
        return {
            "session_code": self.session_code,
            "mode": self.mode,
            "status": self.status,
            "duration": self.duration,
            "remaining_seconds": current_rem,
            "started_at": self.started_at,
            "target_end_time": self.target_end_time,
            "completed_sessions": self.completed_sessions,
            "total_focus_sessions": self.total_focus_sessions,
            "total_completed_cycles": self.total_completed_cycles,
            "total_focus_time_seconds": self.total_focus_time_seconds,
            "updated_at": self.updated_at,
            "server_time": time.time()
        }
