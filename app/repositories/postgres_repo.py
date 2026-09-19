import psycopg
from psycopg.rows import dict_row
from typing import Optional, List
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.room import Room
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings

class PostgresRepository(BaseRepository):
    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        return psycopg.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            dbname=self.db_config['database'],
            sslmode=self.db_config.get('sslmode', 'require'),
            autocommit=True,
            connect_timeout=10
        )

    def create_room(self, room: Room) -> Room:
        sql = """
            INSERT INTO rooms (room_code, creator_token, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (room_code) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = EXCLUDED.updated_at
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    room.room_code, room.creator_token, room.status,
                    room.created_at, room.updated_at
                ))
            return room
        finally:
            conn.close()

    def get_room(self, room_code: str) -> Optional[Room]:
        sql = "SELECT * FROM rooms WHERE room_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (room_code,))
                row = cursor.fetchone()
                if row:
                    return Room(
                        room_code=row['room_code'],
                        creator_token=row['creator_token'],
                        status=row['status'],
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at'])
                    )
            return None
        finally:
            conn.close()

    def delete_room(self, room_code: str) -> bool:
        sql = "DELETE FROM rooms WHERE room_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (room_code,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def add_participant(self, participant: Participant) -> Participant:
        sql = """
            INSERT INTO participants (participant_token, room_code, username, slot, is_online, sid, joined_at, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (participant_token) DO UPDATE SET
            username = EXCLUDED.username,
            slot = EXCLUDED.slot,
            is_online = EXCLUDED.is_online,
            sid = EXCLUDED.sid,
            last_seen = EXCLUDED.last_seen
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    participant.participant_token, participant.room_code, participant.username,
                    participant.slot, bool(participant.is_online), participant.sid,
                    participant.joined_at, participant.last_seen
                ))
            return participant
        finally:
            conn.close()

    def get_participant(self, participant_token: str) -> Optional[Participant]:
        sql = "SELECT * FROM participants WHERE participant_token = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (participant_token,))
                row = cursor.fetchone()
                if row:
                    return Participant(
                        participant_token=row['participant_token'],
                        room_code=row['room_code'],
                        username=row['username'],
                        slot=row['slot'],
                        is_online=bool(row['is_online']),
                        sid=row.get('sid'),
                        joined_at=str(row['joined_at']),
                        last_seen=str(row['last_seen'])
                    )
            return None
        finally:
            conn.close()

    def get_participants_by_room(self, room_code: str) -> List[Participant]:
        sql = "SELECT * FROM participants WHERE room_code = %s ORDER BY slot ASC"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (room_code,))
                rows = cursor.fetchall()
                return [
                    Participant(
                        participant_token=row['participant_token'],
                        room_code=row['room_code'],
                        username=row['username'],
                        slot=row['slot'],
                        is_online=bool(row['is_online']),
                        sid=row.get('sid'),
                        joined_at=str(row['joined_at']),
                        last_seen=str(row['last_seen'])
                    ) for row in rows
                ]
        finally:
            conn.close()

    def update_participant_presence(self, participant_token: str, is_online: bool, sid: Optional[str] = None) -> Optional[Participant]:
        p = self.get_participant(participant_token)
        if not p:
            return None
        
        p.is_online = bool(is_online)
        if sid is not None:
            p.sid = sid
        p.last_seen = datetime.utcnow().isoformat()
        
        sql = "UPDATE participants SET is_online = %s, sid = %s, last_seen = %s WHERE participant_token = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (p.is_online, p.sid, p.last_seen, participant_token))
            return p
        finally:
            conn.close()

    def get_participant_by_sid(self, sid: str) -> Optional[Participant]:
        sql = "SELECT * FROM participants WHERE sid = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (sid,))
                row = cursor.fetchone()
                if row:
                    return Participant(
                        participant_token=row['participant_token'],
                        room_code=row['room_code'],
                        username=row['username'],
                        slot=row['slot'],
                        is_online=bool(row['is_online']),
                        sid=row.get('sid'),
                        joined_at=str(row['joined_at']),
                        last_seen=str(row['last_seen'])
                    )
            return None
        finally:
            conn.close()

    def remove_participant(self, participant_token: str) -> bool:
        sql = "DELETE FROM participants WHERE participant_token = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (participant_token,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_timer(self, room_code: str) -> Optional[TimerState]:
        sql = "SELECT * FROM timers WHERE room_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (room_code,))
                row = cursor.fetchone()
                if row:
                    return TimerState(
                        room_code=row['room_code'],
                        mode=row['mode'],
                        status=row['status'],
                        duration=row['duration'],
                        remaining_seconds=row['remaining_seconds'],
                        started_at=row['started_at'],
                        target_end_time=row['target_end_time'],
                        completed_sessions=row['completed_sessions'],
                        updated_at=row['updated_at']
                    )
            return None
        finally:
            conn.close()

    def save_timer(self, timer: TimerState) -> TimerState:
        sql = """
            INSERT INTO timers (room_code, mode, status, duration, remaining_seconds, started_at, target_end_time, completed_sessions, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (room_code) DO UPDATE SET
            mode = EXCLUDED.mode,
            status = EXCLUDED.status,
            duration = EXCLUDED.duration,
            remaining_seconds = EXCLUDED.remaining_seconds,
            started_at = EXCLUDED.started_at,
            target_end_time = EXCLUDED.target_end_time,
            completed_sessions = EXCLUDED.completed_sessions,
            updated_at = EXCLUDED.updated_at
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    timer.room_code, timer.mode, timer.status, timer.duration, timer.remaining_seconds,
                    timer.started_at, timer.target_end_time, timer.completed_sessions, timer.updated_at
                ))
            return timer
        finally:
            conn.close()

    def get_settings(self, room_code: str) -> Optional[RoomSettings]:
        sql = "SELECT * FROM settings WHERE room_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (room_code,))
                row = cursor.fetchone()
                if row:
                    return RoomSettings(
                        room_code=row['room_code'],
                        focus_duration=row['focus_duration'],
                        short_break_duration=row['short_break_duration'],
                        long_break_duration=row['long_break_duration'],
                        auto_start=bool(row['auto_start']),
                        sound_enabled=bool(row['sound_enabled'])
                    )
            return None
        finally:
            conn.close()

    def save_settings(self, settings: RoomSettings) -> RoomSettings:
        sql = """
            INSERT INTO settings (room_code, focus_duration, short_break_duration, long_break_duration, auto_start, sound_enabled)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (room_code) DO UPDATE SET
            focus_duration = EXCLUDED.focus_duration,
            short_break_duration = EXCLUDED.short_break_duration,
            long_break_duration = EXCLUDED.long_break_duration,
            auto_start = EXCLUDED.auto_start,
            sound_enabled = EXCLUDED.sound_enabled
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    settings.room_code, settings.focus_duration, settings.short_break_duration, settings.long_break_duration,
                    bool(settings.auto_start), bool(settings.sound_enabled)
                ))
            return settings
        finally:
            conn.close()
