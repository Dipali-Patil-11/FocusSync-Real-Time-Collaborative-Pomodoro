from typing import Tuple, Optional
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.repositories.base import BaseRepository
from app.models.user import User
from app.utilities.validators import validate_username

class AuthService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        return self.register(username, email, password)

    def login_user(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        return self.login(username_or_email, password)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.get_user(user_id)

    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        return check_password_hash(password_hash, password)

    def register(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        valid_user, user_msg = validate_username(username)
        if not valid_user:
            return False, user_msg, None

        if not email or '@' not in email or '.' not in email:
            return False, "Invalid email address format.", None

        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        # Check duplicate email
        if self.repo.get_user_by_email(email):
            return False, "An account with this email address already exists.", None

        # Check duplicate username
        if self.repo.get_user_by_username(user_msg):
            return False, "Username is already taken. Please choose another.", None

        pwd_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(
            username=user_msg,
            email=email.strip().lower(),
            password_hash=pwd_hash,
            last_login_at=datetime.utcnow().isoformat()
        )
        saved_user = self.repo.create_user(user)
        return True, "Account registered successfully.", saved_user

    def login(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        if not username_or_email or not password:
            return False, "Username/Email and password are required.", None

        query = username_or_email.strip()
        user = self.repo.get_user_by_email(query) or self.repo.get_user_by_username(query)
        if not user or not check_password_hash(user.password_hash, password):
            # Generic error message to prevent user enumeration
            return False, "Invalid username/email or password.", None

        if not user.is_active:
            return False, "Account is disabled.", None

        user.last_login_at = datetime.utcnow().isoformat()
        user.updated_at = datetime.utcnow().isoformat()
        self.repo.update_user(user)

        return True, "Login successful.", user

    def get_user(self, user_id: str) -> Optional[User]:
        if not user_id:
            return None
        return self.repo.get_user_by_id(user_id)

