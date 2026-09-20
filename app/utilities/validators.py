import re
from app.utilities.constants import MIN_DURATION_MINUTES, MAX_DURATION_MINUTES

def validate_username(username: str) -> tuple[bool, str]:
    if not username or not isinstance(username, str):
        return False, "Username is required."
    
    cleaned = username.strip()
    if len(cleaned) < 2:
        return False, "Username must be at least 2 characters long."
    if len(cleaned) > 20:
        return False, "Username must be 20 characters or less."
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', cleaned):
        return False, "Username contains invalid characters."
        
    return True, cleaned

def validate_session_code(code: str) -> tuple[bool, str]:
    if not code or not isinstance(code, str):
        return False, "Session code is required."
        
    cleaned = code.strip().upper()
    if not re.match(r'^[A-Z0-9]{6}$', cleaned):
        return False, "Session code must be exactly 6 alphanumeric characters."
        
    return True, cleaned

def validate_duration(duration: int, field_name: str = "Duration") -> tuple[bool, str]:
    try:
        val = int(duration)
        if val < MIN_DURATION_MINUTES or val > MAX_DURATION_MINUTES:
            return False, f"{field_name} must be between {MIN_DURATION_MINUTES} and {MAX_DURATION_MINUTES} minutes."
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid value for {field_name}."

def validate_interval(interval: int, field_name: str = "Long break interval") -> tuple[bool, str]:
    try:
        val = int(interval)
        if val < 2 or val > 8:
            return False, f"{field_name} must be between 2 and 8 focus sessions."
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid value for {field_name}."

