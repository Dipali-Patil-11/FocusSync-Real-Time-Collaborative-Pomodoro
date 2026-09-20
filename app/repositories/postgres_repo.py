import psycopg
from psycopg.rows import dict_row
from typing import Optional, List
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.session import Session
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import SessionSettings
from app.models.user import User
from app.models.history import UserSessionHistory

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

    def create_session(self, session: Session) -> Session:
        sql = """
            INSERT INTO sessions (session_code, creator_token, session_id, creator_user_id, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_code) DO UPDATE SET
            status = EXCLUDED.status,
            creator_user_id = EXCLUDED.creator_user_id,
            updated_at = EXCLUDED.updated_at
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    session.session_code, session.creator_token, session.session_id, session.creator_user_id, session.status,
                    session.created_at, session.updated_at
                ))
            return session
        finally:
            conn.close()

    def get_session(self, session_code: str) -> Optional[Session]:
        sql = "SELECT * FROM sessions WHERE session_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (session_code,))
                row = cursor.fetchone()
                if row:
                    return Session(
                        session_code=row['session_code'],
                        creator_token=row['creator_token'],
                        session_id=row.get('session_id', ''),
                        creator_user_id=row.get('creator_user_id'),
                        status=row['status'],
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at'])
                    )
            return None
        finally:
            conn.close()

    def delete_session(self, session_code: str) -> bool:
        sql = "DELETE FROM sessions WHERE session_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (session_code,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def add_participant(self, participant: Participant) -> Participant:
        sql = """
            INSERT INTO participants (participant_token, session_code, user_id, username, slot, is_online, sid, joined_at, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (participant_token) DO UPDATE SET
            user_id = EXCLUDED.user_id,
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
                    participant.participant_token, participant.session_code, participant.user_id,
                    participant.username, participant.slot, bool(participant.is_online),
                    participant.sid, participant.joined_at, participant.last_seen
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
                        session_code=row['session_code'],
                        user_id=row.get('user_id'),
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

    def get_participants_by_session(self, session_code: str) -> List[Participant]:
        sql = "SELECT * FROM participants WHERE session_code = %s ORDER BY slot ASC"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (session_code,))
                rows = cursor.fetchall()
                return [
                    Participant(
                        participant_token=row['participant_token'],
                        session_code=row['session_code'],
                        user_id=row.get('user_id'),
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
                        session_code=row['session_code'],
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

    def get_timer(self, session_code: str) -> Optional[TimerState]:
        sql = "SELECT * FROM timers WHERE session_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (session_code,))
                row = cursor.fetchone()
                if row:
                    return TimerState(
                        session_code=row['session_code'],
                        mode=row['mode'],
                        status=row['status'],
                        duration=row['duration'],
                        remaining_seconds=row['remaining_seconds'],
                        started_at=row['started_at'],
                        target_end_time=row['target_end_time'],
                        completed_sessions=row['completed_sessions'],
                        total_focus_sessions=row.get('total_focus_sessions', 0) if row.get('total_focus_sessions') is not None else 0,
                        total_completed_cycles=row.get('total_completed_cycles', 0) if row.get('total_completed_cycles') is not None else 0,
                        total_focus_time_seconds=row.get('total_focus_time_seconds', 0) if row.get('total_focus_time_seconds') is not None else 0,
                        updated_at=row['updated_at']
                    )
            return None
        finally:
            conn.close()

    def save_timer(self, timer: TimerState) -> TimerState:
        sql = """
            INSERT INTO timers (session_code, mode, status, duration, remaining_seconds, started_at, target_end_time, completed_sessions, total_focus_sessions, total_completed_cycles, total_focus_time_seconds, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_code) DO UPDATE SET
            mode = EXCLUDED.mode,
            status = EXCLUDED.status,
            duration = EXCLUDED.duration,
            remaining_seconds = EXCLUDED.remaining_seconds,
            started_at = EXCLUDED.started_at,
            target_end_time = EXCLUDED.target_end_time,
            completed_sessions = EXCLUDED.completed_sessions,
            total_focus_sessions = EXCLUDED.total_focus_sessions,
            total_completed_cycles = EXCLUDED.total_completed_cycles,
            total_focus_time_seconds = EXCLUDED.total_focus_time_seconds,
            updated_at = EXCLUDED.updated_at
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    timer.session_code, timer.mode, timer.status, timer.duration, timer.remaining_seconds,
                    timer.started_at, timer.target_end_time, timer.completed_sessions,
                    timer.total_focus_sessions, timer.total_completed_cycles, timer.total_focus_time_seconds,
                    timer.updated_at
                ))
            return timer
        finally:
            conn.close()

    def get_settings(self, session_code: str) -> Optional[SessionSettings]:
        sql = "SELECT * FROM settings WHERE session_code = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (session_code,))
                row = cursor.fetchone()
                if row:
                    return SessionSettings(
                        session_code=row['session_code'],
                        focus_duration=row['focus_duration'],
                        short_break_duration=row['short_break_duration'],
                        long_break_duration=row['long_break_duration'],
                        long_break_interval=row.get('long_break_interval', 4) if 'long_break_interval' in row and row['long_break_interval'] is not None else 4,
                        auto_start=bool(row['auto_start']),
                        sound_enabled=bool(row['sound_enabled'])
                    )
            return None
        finally:
            conn.close()

    def save_settings(self, settings: SessionSettings) -> SessionSettings:
        sql = """
            INSERT INTO settings (session_code, focus_duration, short_break_duration, long_break_duration, long_break_interval, auto_start, sound_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_code) DO UPDATE SET
            focus_duration = EXCLUDED.focus_duration,
            short_break_duration = EXCLUDED.short_break_duration,
            long_break_duration = EXCLUDED.long_break_duration,
            long_break_interval = EXCLUDED.long_break_interval,
            auto_start = EXCLUDED.auto_start,
            sound_enabled = EXCLUDED.sound_enabled
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    settings.session_code, settings.focus_duration, settings.short_break_duration, settings.long_break_duration,
                    settings.long_break_interval, bool(settings.auto_start), bool(settings.sound_enabled)
                ))
            return settings
        finally:
            conn.close()

    # User operations
    def create_user(self, user: User) -> User:
        sql = """
            INSERT INTO users (user_id, username, email, password_hash, is_active, created_at, updated_at, last_login_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
            username = EXCLUDED.username,
            email = EXCLUDED.email,
            password_hash = EXCLUDED.password_hash,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at,
            last_login_at = EXCLUDED.last_login_at
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    user.user_id, user.username, user.email, user.password_hash,
                    user.is_active, user.created_at, user.updated_at, user.last_login_at
                ))
            return user
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        sql = "SELECT * FROM users WHERE user_id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
                if row:
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        password_hash=row['password_hash'],
                        is_active=bool(row['is_active']),
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at']),
                        last_login_at=str(row['last_login_at']) if row.get('last_login_at') else None
                    )
            return None
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        sql = "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (email,))
                row = cursor.fetchone()
                if row:
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        password_hash=row['password_hash'],
                        is_active=bool(row['is_active']),
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at']),
                        last_login_at=str(row['last_login_at']) if row.get('last_login_at') else None
                    )
            return None
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[User]:
        sql = "SELECT * FROM users WHERE LOWER(username) = LOWER(%s)"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (username,))
                row = cursor.fetchone()
                if row:
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        password_hash=row['password_hash'],
                        is_active=bool(row['is_active']),
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at']),
                        last_login_at=str(row['last_login_at']) if row.get('last_login_at') else None
                    )
            return None
        finally:
            conn.close()

    def update_user(self, user: User) -> User:
        return self.create_user(user)

    def clear_user_id_from_participants(self, user_id: str) -> List[str]:
        sql_sel = "SELECT DISTINCT session_code FROM participants WHERE user_id = %s"
        sql_upd = "UPDATE participants SET user_id = NULL WHERE user_id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql_sel, (user_id,))
                rows = cursor.fetchall()
                codes = [r['session_code'] for r in rows]
                cursor.execute(sql_upd, (user_id,))
                return codes
        finally:
            conn.close()

    # History operations
    def save_user_history(self, history: UserSessionHistory) -> UserSessionHistory:
        sql = """
            INSERT INTO user_session_history (history_id, user_id, session_code, session_id, role, joined_at, left_at, focus_sessions_completed, focus_time_seconds, current_cycle_focus_sessions, cycles_completed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, session_id) DO UPDATE SET
            role = EXCLUDED.role,
            left_at = EXCLUDED.left_at,
            focus_sessions_completed = EXCLUDED.focus_sessions_completed,
            focus_time_seconds = EXCLUDED.focus_time_seconds,
            current_cycle_focus_sessions = EXCLUDED.current_cycle_focus_sessions,
            cycles_completed = EXCLUDED.cycles_completed
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    history.history_id, history.user_id, history.session_code, history.session_id, history.role,
                    history.joined_at, history.left_at, history.focus_sessions_completed,
                    history.focus_time_seconds, history.current_cycle_focus_sessions, history.cycles_completed
                ))
            return history
        finally:
            conn.close()

    def get_user_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[UserSessionHistory]:
        sql = "SELECT * FROM user_session_history WHERE user_id = %s ORDER BY joined_at DESC LIMIT %s OFFSET %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (user_id, limit, offset))
                rows = cursor.fetchall()
                return [
                    UserSessionHistory(
                        history_id=row['history_id'],
                        user_id=row['user_id'],
                        session_code=row['session_code'],
                        session_id=row.get('session_id', ''),
                        role=row['role'],
                        joined_at=str(row['joined_at']),
                        left_at=str(row['left_at']) if row.get('left_at') else None,
                        focus_sessions_completed=row['focus_sessions_completed'],
                        focus_time_seconds=row['focus_time_seconds'],
                        current_cycle_focus_sessions=row.get('current_cycle_focus_sessions', 0),
                        cycles_completed=row['cycles_completed']
                    ) for row in rows
                ]
        finally:
            conn.close()

    def get_user_history_entry(self, user_id: str, session_id: str) -> Optional[UserSessionHistory]:
        sql = "SELECT * FROM user_session_history WHERE user_id = %s AND session_id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (user_id, session_id))
                row = cursor.fetchone()
                if row:
                    return UserSessionHistory(
                        history_id=row['history_id'],
                        user_id=row['user_id'],
                        session_code=row['session_code'],
                        session_id=row.get('session_id', ''),
                        role=row['role'],
                        joined_at=str(row['joined_at']),
                        left_at=str(row['left_at']) if row.get('left_at') else None,
                        focus_sessions_completed=row['focus_sessions_completed'],
                        focus_time_seconds=row['focus_time_seconds'],
                        current_cycle_focus_sessions=row.get('current_cycle_focus_sessions', 0),
                        cycles_completed=row['cycles_completed']
                    )
            return None
        finally:
            conn.close()
