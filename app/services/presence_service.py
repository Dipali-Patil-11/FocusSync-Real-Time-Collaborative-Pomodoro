from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.participant import Participant

class PresenceService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository

    def set_online(self, participant_token: str, sid: str) -> Optional[Participant]:
        return self.repo.update_participant_presence(participant_token, is_online=True, sid=sid)

    def set_offline(self, participant_token: str) -> Optional[Participant]:
        return self.repo.update_participant_presence(participant_token, is_online=False, sid=None)

    def set_offline_by_sid(self, sid: str) -> Optional[Participant]:
        p = self.repo.get_participant_by_sid(sid)
        if p:
            return self.repo.update_participant_presence(p.participant_token, is_online=False, sid=None)
        return None

    def get_room_participants(self, room_code: str) -> List[Participant]:
        return self.repo.get_participants_by_room(room_code)
