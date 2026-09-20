import uuid
from dataclasses import dataclass, field
from datetime import datetime
import secrets
import string

def generate_session_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))

@dataclass
class Session:
    session_code: str
    creator_token: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creator_user_id: str = None
    status: str = "ACTIVE"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "session_code": self.session_code,
            "creator_token": self.creator_token,
            "creator_user_id": self.creator_user_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

