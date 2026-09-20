from dataclasses import dataclass, field
from datetime import datetime
import uuid
from typing import Optional

@dataclass
class UserSessionHistory:
    history_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    session_code: str = ""
    session_id: str = ""
    role: str = "PARTICIPANT"  # 'CREATOR' or 'PARTICIPANT'
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    left_at: Optional[str] = None
    focus_sessions_completed: int = 0
    focus_time_seconds: int = 0
    current_cycle_focus_sessions: int = 0
    cycles_completed: int = 0

    def to_dict(self):
        return {
            "history_id": self.history_id,
            "user_id": self.user_id,
            "session_code": self.session_code,
            "session_id": self.session_id,
            "role": self.role,
            "joined_at": self.joined_at,
            "left_at": self.left_at,
            "focus_sessions_completed": self.focus_sessions_completed,
            "focus_time_seconds": self.focus_time_seconds,
            "current_cycle_focus_sessions": self.current_cycle_focus_sessions,
            "cycles_completed": self.cycles_completed
        }

