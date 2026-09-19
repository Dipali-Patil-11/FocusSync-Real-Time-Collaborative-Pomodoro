from dataclasses import dataclass, field
from datetime import datetime
import secrets
import string

def generate_room_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    # Exclude confusing characters like O, 0, I, 1 if desired, but 6-char standard:
    return ''.join(secrets.choice(alphabet) for _ in range(6))

@dataclass
class Room:
    room_code: str
    creator_token: str
    status: str = "ACTIVE"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            "room_code": self.room_code,
            "creator_token": self.creator_token,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
