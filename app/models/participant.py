from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Participant:
    participant_token: str
    session_code: str
    username: str
    slot: int  # 1 or 2
    is_online: bool = True
    sid: str = None
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            "participant_token": self.participant_token,
            "session_code": self.session_code,
            "username": self.username,
            "slot": self.slot,
            "is_online": self.is_online,
            "joined_at": self.joined_at,
            "last_seen": self.last_seen
        }
