from typing import List, Dict, Any, Optional
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.history import UserSessionHistory

class HistoryService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository

    def record_session_join(self, user_id: str, session_code: str, session_id: str, role: str = "PARTICIPANT") -> Optional[UserSessionHistory]:
        if not user_id or not session_code or not session_id:
            return None
        
        entry = self.repo.get_user_history_entry(user_id, session_id)
        if not entry:
            entry = UserSessionHistory(
                user_id=user_id,
                session_code=session_code,
                session_id=session_id,
                role=role,
                joined_at=datetime.utcnow().isoformat()
            )
            return self.repo.save_user_history(entry)
        else:
            # Re-joining room, clear left_at
            entry.left_at = None
            return self.repo.save_user_history(entry)

    def record_session_leave(self, user_id: str, session_id: str) -> Optional[UserSessionHistory]:
        if not user_id or not session_id:
            return None
        
        entry = self.repo.get_user_history_entry(user_id, session_id)
        if entry:
            entry.left_at = datetime.utcnow().isoformat()
            return self.repo.save_user_history(entry)
        return None

    def credit_focus_run(self, session_code: str, session_id: str, eligible_user_ids: set, duration_secs: int, long_break_interval: int = 4):
        """
        Credit logged-in participants who were eligible when the timer run started.
        Uses per-user cycle attribution based on each user's completed focus sessions.
        """
        if not session_code or not session_id or not eligible_user_ids:
            return

        for user_id in eligible_user_ids:
            if not user_id:
                continue
            entry = self.repo.get_user_history_entry(user_id, session_id)
            if not entry:
                entry = UserSessionHistory(user_id=user_id, session_code=session_code, session_id=session_id)
            
            entry.focus_sessions_completed += 1
            entry.focus_time_seconds += duration_secs
            entry.current_cycle_focus_sessions += 1

            if entry.current_cycle_focus_sessions >= long_break_interval:
                entry.cycles_completed += 1
                entry.current_cycle_focus_sessions = 0
            
            self.repo.save_user_history(entry)

    def get_user_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        entries = self.repo.get_user_history(user_id, limit, offset)
        return [e.to_dict() for e in entries]

    def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        entries = self.repo.get_user_history(user_id, limit=50, offset=0)
        
        total_focus_sessions = sum(e.focus_sessions_completed for e in entries)
        total_focus_time_seconds = sum(e.focus_time_seconds for e in entries)
        total_cycles_completed = sum(e.cycles_completed for e in entries)
        total_rooms_joined = len(entries)

        recent_sessions = [e.to_dict() for e in entries[:5]]

        return {
            "total_focus_sessions": total_focus_sessions,
            "total_focus_time_seconds": total_focus_time_seconds,
            "total_completed_cycles": total_cycles_completed,
            "total_rooms_joined": total_rooms_joined,
            "recent_sessions": recent_sessions
        }
