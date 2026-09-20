from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class User:
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_login_at: str = None

    def to_dict(self, include_sensitive=False):
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login_at": self.last_login_at
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data
