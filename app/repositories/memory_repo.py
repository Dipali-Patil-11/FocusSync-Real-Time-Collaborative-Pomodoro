from typing import Optional, List, Dict
import threading
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.room import Room
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings

class MemoryRepository(BaseRepository):
    def __init__(self):
        self._lock = threading.RLock()
        self._rooms: Dict[str, Room] = {}
        self._participants: Dict[str, Participant] = {}  # key: participant_token
        self._timers: Dict[str, TimerState] = {}          # key: room_code
        self._settings: Dict[str, RoomSettings] = {}      # key: room_code

    def create_room(self, room: Room) -> Room:
        with self._lock:
            self._rooms[room.room_code] = room
            return room

    def get_room(self, room_code: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_code)

    def delete_room(self, room_code: str) -> bool:
        with self._lock:
            if room_code in self._rooms:
                del self._rooms[room_code]
                # Clean up associated participants, timer, settings
                tokens_to_del = [t for t, p in self._participants.items() if p.room_code == room_code]
                for t in tokens_to_del:
                    del self._participants[t]
                self._timers.pop(room_code, None)
                self._settings.pop(room_code, None)
                return True
            return False

    def add_participant(self, participant: Participant) -> Participant:
        with self._lock:
            self._participants[participant.participant_token] = participant
            return participant

    def get_participant(self, participant_token: str) -> Optional[Participant]:
        with self._lock:
            return self._participants.get(participant_token)

    def get_participants_by_room(self, room_code: str) -> List[Participant]:
        with self._lock:
            return [p for p in self._participants.values() if p.room_code == room_code]

    def update_participant_presence(self, participant_token: str, is_online: bool, sid: Optional[str] = None) -> Optional[Participant]:
        with self._lock:
            participant = self._participants.get(participant_token)
            if participant:
                participant.is_online = is_online
                if sid is not None:
                    participant.sid = sid
                participant.last_seen = datetime.utcnow().isoformat()
                return participant
            return None

    def get_participant_by_sid(self, sid: str) -> Optional[Participant]:
        with self._lock:
            for p in self._participants.values():
                if p.sid == sid:
                    return p
            return None

    def remove_participant(self, participant_token: str) -> bool:
        with self._lock:
            if participant_token in self._participants:
                del self._participants[participant_token]
                return True
            return False

    def get_timer(self, room_code: str) -> Optional[TimerState]:
        with self._lock:
            return self._timers.get(room_code)

    def save_timer(self, timer: TimerState) -> TimerState:
        with self._lock:
            self._timers[timer.room_code] = timer
            return timer

    def get_settings(self, room_code: str) -> Optional[RoomSettings]:
        with self._lock:
            return self._settings.get(room_code)

    def save_settings(self, settings: RoomSettings) -> RoomSettings:
        with self._lock:
            self._settings[settings.room_code] = settings
            return settings
