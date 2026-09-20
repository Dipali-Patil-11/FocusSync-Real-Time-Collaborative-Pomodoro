from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.session import Session
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import SessionSettings

class BaseRepository(ABC):

    # Session operations
    @abstractmethod
    def create_session(self, session: Session) -> Session:
        pass

    @abstractmethod
    def get_session(self, session_code: str) -> Optional[Session]:
        pass

    @abstractmethod
    def delete_session(self, session_code: str) -> bool:
        pass

    # Participant operations
    @abstractmethod
    def add_participant(self, participant: Participant) -> Participant:
        pass

    @abstractmethod
    def get_participant(self, participant_token: str) -> Optional[Participant]:
        pass

    @abstractmethod
    def get_participants_by_session(self, session_code: str) -> List[Participant]:
        pass

    @abstractmethod
    def update_participant_presence(self, participant_token: str, is_online: bool, sid: Optional[str] = None) -> Optional[Participant]:
        pass

    @abstractmethod
    def get_participant_by_sid(self, sid: str) -> Optional[Participant]:
        pass

    @abstractmethod
    def remove_participant(self, participant_token: str) -> bool:
        pass

    # Timer operations
    @abstractmethod
    def get_timer(self, session_code: str) -> Optional[TimerState]:
        pass

    @abstractmethod
    def save_timer(self, timer: TimerState) -> TimerState:
        pass

    # Settings operations
    @abstractmethod
    def get_settings(self, session_code: str) -> Optional[SessionSettings]:
        pass

    @abstractmethod
    def save_settings(self, settings: SessionSettings) -> SessionSettings:
        pass
