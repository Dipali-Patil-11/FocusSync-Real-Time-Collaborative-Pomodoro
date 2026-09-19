import uuid
from typing import Tuple, Optional, Dict, Any
from app.repositories.base import BaseRepository
from app.models.room import Room, generate_room_code
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings
from app.services.timer_service import TimerService
from app.services.settings_service import SettingsService
from app.utilities.constants import MAX_PARTICIPANTS
from app.utilities.validators import validate_username, validate_room_code

class RoomService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository
        self.timer_service = TimerService(repository)
        self.settings_service = SettingsService(repository)

    def create_room(self, username: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valid_user, user_msg = validate_username(username)
        if not valid_user:
            return False, user_msg, None

        # Generate unique room code
        for _ in range(10):
            code = generate_room_code()
            if not self.repo.get_room(code):
                break
        else:
            return False, "Failed to generate unique room code", None

        creator_token = str(uuid.uuid4())
        room = Room(room_code=code, creator_token=creator_token)
        self.repo.create_room(room)

        # Create slot 1 participant
        participant = Participant(
            participant_token=creator_token,
            room_code=code,
            username=user_msg,
            slot=1,
            is_online=True
        )
        self.repo.add_participant(participant)

        # Initialize settings & timer
        settings = self.settings_service.get_or_create_settings(code)
        timer = self.timer_service.get_or_create_timer(code, settings)

        return True, "Room created successfully", {
            "room_code": code,
            "participant_token": creator_token,
            "participant": participant.to_dict(),
            "room": room.to_dict(),
            "timer": timer.to_dict(),
            "settings": settings.to_dict()
        }

    def join_room(self, room_code: str, username: str, participant_token: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]], str]:
        """
        Returns: (success, message, room_data, status_code)
        status_code can be 'OK', 'NOT_FOUND', 'FULL', 'INVALID'
        """
        valid_code, code_msg = validate_room_code(room_code)
        if not valid_code:
            return False, code_msg, None, 'INVALID'

        valid_user, user_msg = validate_username(username)
        if not valid_user:
            return False, user_msg, None, 'INVALID'

        room = self.repo.get_room(code_msg)
        if not room:
            return False, f"Room {code_msg} not found.", None, 'NOT_FOUND'

        existing_participants = self.repo.get_participants_by_room(code_msg)

        # Reconnection check
        if participant_token:
            for p in existing_participants:
                if p.participant_token == participant_token:
                    p.username = user_msg
                    p.is_online = True
                    self.repo.add_participant(p)
                    settings = self.settings_service.get_or_create_settings(code_msg)
                    timer = self.timer_service.get_or_create_timer(code_msg, settings)
                    return True, "Rejoined room", {
                        "room_code": code_msg,
                        "participant_token": participant_token,
                        "participant": p.to_dict(),
                        "room": room.to_dict(),
                        "timer": timer.to_dict(),
                        "settings": settings.to_dict(),
                        "participants": [pt.to_dict() for pt in self.repo.get_participants_by_room(code_msg)]
                    }, 'OK'

        # Strict 2 participant capacity check
        if len(existing_participants) >= MAX_PARTICIPANTS:
            return False, f"Room {code_msg} is full (Maximum {MAX_PARTICIPANTS} participants).", None, 'FULL'

        # Assign available slot (1 or 2)
        used_slots = {p.slot for p in existing_participants}
        slot = 1 if 1 not in used_slots else 2

        new_token = str(uuid.uuid4())
        participant = Participant(
            participant_token=new_token,
            room_code=code_msg,
            username=user_msg,
            slot=slot,
            is_online=True
        )
        self.repo.add_participant(participant)

        settings = self.settings_service.get_or_create_settings(code_msg)
        timer = self.timer_service.get_or_create_timer(code_msg, settings)

        return True, "Joined room successfully", {
            "room_code": code_msg,
            "participant_token": new_token,
            "participant": participant.to_dict(),
            "room": room.to_dict(),
            "timer": timer.to_dict(),
            "settings": settings.to_dict(),
            "participants": [pt.to_dict() for pt in self.repo.get_participants_by_room(code_msg)]
        }, 'OK'

    def get_room_state(self, room_code: str) -> Optional[Dict[str, Any]]:
        room = self.repo.get_room(room_code)
        if not room:
            return None
        participants = self.repo.get_participants_by_room(room_code)
        settings = self.settings_service.get_or_create_settings(room_code)
        timer = self.timer_service.get_or_create_timer(room_code, settings)

        return {
            "room_code": room_code,
            "room": room.to_dict(),
            "participants": [p.to_dict() for p in participants],
            "timer": timer.to_dict(),
            "settings": settings.to_dict()
        }

    def leave_room(self, participant_token: str) -> Tuple[bool, str, Optional[str]]:
        participant = self.repo.get_participant(participant_token)
        if not participant:
            return False, "Participant not found", None

        room_code = participant.room_code
        self.repo.remove_participant(participant_token)

        remaining = self.repo.get_participants_by_room(room_code)
        if not remaining:
            self.repo.delete_room(room_code)

        return True, "Left room successfully", room_code
