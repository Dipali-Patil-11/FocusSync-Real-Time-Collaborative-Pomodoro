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
        self._users: Dict[str, any] = {}                     # key: user_id
        self._history: Dict[str, any] = {}                   # key: history_id

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

    # User operations
    def create_user(self, user):
        with self._lock:
            self._users[user.user_id] = user
            return user

    def get_user_by_id(self, user_id: str):
        with self._lock:
            return self._users.get(user_id)

    def get_user_by_email(self, email: str):
        with self._lock:
            email_lower = email.lower()
            for u in self._users.values():
                if u.email.lower() == email_lower:
                    return u
            return None

    def get_user_by_username(self, username: str):
        with self._lock:
            u_lower = username.lower()
            for u in self._users.values():
                if u.username.lower() == u_lower:
                    return u
            return None

    def update_user(self, user):
        with self._lock:
            self._users[user.user_id] = user
            return user

    def clear_user_id_from_participants(self, user_id: str) -> List[str]:
        with self._lock:
            affected_codes = set()
            for p in self._participants.values():
                if p.user_id == user_id:
                    p.user_id = None
                    affected_codes.add(p.session_code)
            return list(affected_codes)

    # History operations
    def save_user_history(self, history):
        with self._lock:
            self._history[history.history_id] = history
            return history

    def get_user_history(self, user_id: str, limit: int = 50, offset: int = 0):
        with self._lock:
            user_entries = [h for h in self._history.values() if h.user_id == user_id]
            # Sort descending by joined_at
            user_entries.sort(key=lambda x: x.joined_at, reverse=True)
            return user_entries[offset:offset + limit]

    def get_user_history_entry(self, user_id: str, session_id: str):
        with self._lock:
            for h in self._history.values():
                if h.user_id == user_id and h.session_id == session_id:
                    return h
            return None
