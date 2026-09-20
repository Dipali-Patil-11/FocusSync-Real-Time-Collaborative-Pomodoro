import uuid
from typing import Tuple, Optional, Dict, Any
from app.repositories.base import BaseRepository
from app.models.session import Session, generate_session_code
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import SessionSettings
from app.services.timer_service import TimerService
from app.services.settings_service import SettingsService
from app.utilities.constants import MAX_PARTICIPANTS
from app.utilities.validators import validate_username, validate_session_code

class SessionService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository
        self.timer_service = TimerService(repository)
        self.settings_service = SettingsService(repository)

    def create_session(self, username: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valid_user, user_msg = validate_username(username)
        if not valid_user:
            return False, user_msg, None

        # Generate unique session code
        for _ in range(10):
            code = generate_session_code()
            if not self.repo.get_session(code):
                break
        else:
            return False, "Failed to generate unique session code", None

        creator_token = str(uuid.uuid4())
        session = Session(session_code=code, creator_token=creator_token)
        self.repo.create_session(session)

        # Create slot 1 participant
        participant = Participant(
            participant_token=creator_token,
            session_code=code,
            username=user_msg,
            slot=1,
            is_online=True
        )
        self.repo.add_participant(participant)

        # Initialize settings & timer
        settings = self.settings_service.get_or_create_settings(code)
        timer = self.timer_service.get_or_create_timer(code, settings)

        return True, "Session created successfully", {
            "session_code": code,
            "participant_token": creator_token,
            "participant": participant.to_dict(),
            "session": session.to_dict(),
            "timer": timer.to_dict(),
            "settings": settings.to_dict()
        }

    def join_session(self, session_code: str, username: str, participant_token: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]], str]:
        """
        Returns: (success, message, session_data, status_code)
        status_code can be 'OK', 'NOT_FOUND', 'FULL', 'INVALID'
        """
        valid_code, code_msg = validate_session_code(session_code)
        if not valid_code:
            return False, code_msg, None, 'INVALID'

        valid_user, user_msg = validate_username(username)
        if not valid_user:
            return False, user_msg, None, 'INVALID'

        session = self.repo.get_session(code_msg)
        if not session:
            return False, f"Session {code_msg} not found.", None, 'NOT_FOUND'

        existing_participants = self.repo.get_participants_by_session(code_msg)

        # Reconnection check
        if participant_token:
            for p in existing_participants:
                if p.participant_token == participant_token:
                    p.username = user_msg
                    p.is_online = True
                    self.repo.add_participant(p)
                    settings = self.settings_service.get_or_create_settings(code_msg)
                    timer = self.timer_service.get_or_create_timer(code_msg, settings)
                    return True, "Rejoined session", {
                        "session_code": code_msg,
                        "participant_token": participant_token,
                        "participant": p.to_dict(),
                        "session": session.to_dict(),
                        "timer": timer.to_dict(),
                        "settings": settings.to_dict(),
                        "participants": [pt.to_dict() for pt in self.repo.get_participants_by_session(code_msg)]
                    }, 'OK'

        # Strict 2 participant capacity check
        if len(existing_participants) >= MAX_PARTICIPANTS:
            return False, f"Session {code_msg} is full (Maximum {MAX_PARTICIPANTS} participants).", None, 'FULL'

        # Assign available slot (1 or 2)
        used_slots = {p.slot for p in existing_participants}
        slot = 1 if 1 not in used_slots else 2

        new_token = str(uuid.uuid4())
        participant = Participant(
            participant_token=new_token,
            session_code=code_msg,
            username=user_msg,
            slot=slot,
            is_online=True
        )
        self.repo.add_participant(participant)

        settings = self.settings_service.get_or_create_settings(code_msg)
        timer = self.timer_service.get_or_create_timer(code_msg, settings)

        return True, "Joined session successfully", {
            "session_code": code_msg,
            "participant_token": new_token,
            "participant": participant.to_dict(),
            "session": session.to_dict(),
            "timer": timer.to_dict(),
            "settings": settings.to_dict(),
            "participants": [pt.to_dict() for pt in self.repo.get_participants_by_session(code_msg)]
        }, 'OK'

    def get_session_state(self, session_code: str) -> Optional[Dict[str, Any]]:
        session = self.repo.get_session(session_code)
        if not session:
            return None
        participants = self.repo.get_participants_by_session(session_code)
        settings = self.settings_service.get_or_create_settings(session_code)
        timer = self.timer_service.get_or_create_timer(session_code, settings)

        return {
            "session_code": session_code,
            "session": session.to_dict(),
            "participants": [p.to_dict() for p in participants],
            "timer": timer.to_dict(),
            "settings": settings.to_dict()
        }

    def leave_session(self, participant_token: str) -> Tuple[bool, str, Optional[str]]:
        participant = self.repo.get_participant(participant_token)
        if not participant:
            return False, "Participant not found", None

        session_code = participant.session_code
        self.repo.remove_participant(participant_token)

        remaining = self.repo.get_participants_by_session(session_code)
        if not remaining:
            self.repo.delete_session(session_code)

        return True, "Left session successfully", session_code
