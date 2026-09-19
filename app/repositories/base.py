from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.room import Room
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings

class BaseRepository(ABC):

    # Room operations
    @abstractmethod
    def create_room(self, room: Room) -> Room:
        pass

    @abstractmethod
    def get_room(self, room_code: str) -> Optional[Room]:
        pass

    @abstractmethod
    def delete_room(self, room_code: str) -> bool:
        pass

    # Participant operations
    @abstractmethod
    def add_participant(self, participant: Participant) -> Participant:
        pass

    @abstractmethod
    def get_participant(self, participant_token: str) -> Optional[Participant]:
        pass

    @abstractmethod
    def get_participants_by_room(self, room_code: str) -> List[Participant]:
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
    def get_timer(self, room_code: str) -> Optional[TimerState]:
        pass

    @abstractmethod
    def save_timer(self, timer: TimerState) -> TimerState:
        pass

    # Settings operations
    @abstractmethod
    def get_settings(self, room_code: str) -> Optional[RoomSettings]:
        pass

    @abstractmethod
    def save_settings(self, settings: RoomSettings) -> RoomSettings:
        pass
