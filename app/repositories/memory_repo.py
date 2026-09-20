from typing import Optional, List, Dict
import threading
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.session import Session
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import SessionSettings

class MemoryRepository(BaseRepository):
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: Dict[str, Session] = {}
        self._participants: Dict[str, Participant] = {}  # key: participant_token
        self._timers: Dict[str, TimerState] = {}          # key: session_code
        self._settings: Dict[str, SessionSettings] = {}      # key: session_code

    def create_session(self, session: Session) -> Session:
        with self._lock:
            self._sessions[session.session_code] = session
            return session

    def get_session(self, session_code: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_code)

    def delete_session(self, session_code: str) -> bool:
        with self._lock:
            if session_code in self._sessions:
                del self._sessions[session_code]
                # Clean up associated participants, timer, settings
                tokens_to_del = [t for t, p in self._participants.items() if p.session_code == session_code]
                for t in tokens_to_del:
                    del self._participants[t]
                self._timers.pop(session_code, None)
                self._settings.pop(session_code, None)
                return True
            return False

    def add_participant(self, participant: Participant) -> Participant:
        with self._lock:
            self._participants[participant.participant_token] = participant
            return participant

    def get_participant(self, participant_token: str) -> Optional[Participant]:
        with self._lock:
            return self._participants.get(participant_token)

    def get_participants_by_session(self, session_code: str) -> List[Participant]:
        with self._lock:
            return [p for p in self._participants.values() if p.session_code == session_code]

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

    def get_timer(self, session_code: str) -> Optional[TimerState]:
        with self._lock:
            return self._timers.get(session_code)

    def save_timer(self, timer: TimerState) -> TimerState:
        with self._lock:
            self._timers[timer.session_code] = timer
            return timer

    def get_settings(self, session_code: str) -> Optional[SessionSettings]:
        with self._lock:
            return self._settings.get(session_code)

    def save_settings(self, settings: SessionSettings) -> SessionSettings:
        with self._lock:
            self._settings[settings.session_code] = settings
            return settings
