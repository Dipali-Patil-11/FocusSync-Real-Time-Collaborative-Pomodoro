from app.repositories.base import BaseRepository
from app.models.settings import SessionSettings
from app.utilities.validators import validate_duration

class SettingsService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository

    def get_or_create_settings(self, session_code: str) -> SessionSettings:
        settings = self.repo.get_settings(session_code)
        if not settings:
            settings = SessionSettings(session_code=session_code)
            self.repo.save_settings(settings)
        return settings

    def update_settings(self, session_code: str, focus_min: int, short_break_min: int, long_break_min: int, auto_start: bool, sound_enabled: bool) -> tuple[bool, str, SessionSettings]:
        valid, msg = validate_duration(focus_min, "Focus duration")
        if not valid:
            return False, msg, None
            
        valid, msg = validate_duration(short_break_min, "Short break duration")
        if not valid:
            return False, msg, None
            
        valid, msg = validate_duration(long_break_min, "Long break duration")
        if not valid:
            return False, msg, None

        settings = SessionSettings(
            session_code=session_code,
            focus_duration=int(focus_min),
            short_break_duration=int(short_break_min),
            long_break_duration=int(long_break_min),
            auto_start=bool(auto_start),
            sound_enabled=bool(sound_enabled)
        )
        saved = self.repo.save_settings(settings)
        return True, "Settings updated successfully.", saved
