import time
import threading
from typing import Optional, Tuple
from app.repositories.base import BaseRepository
from app.models.timer import TimerState
from app.models.settings import SessionSettings
from app.utilities.constants import TimerMode, TimerStatus

class TimerService:
    def __init__(self, repository: BaseRepository):
        self.repo = repository
        self._lock = threading.RLock()

    def get_or_create_timer(self, session_code: str, settings: Optional[SessionSettings] = None) -> TimerState:
        with self._lock:
            timer = self.repo.get_timer(session_code)
            if not timer:
                focus_duration = (settings.focus_duration if settings else 25) * 60
                timer = TimerState(
                    session_code=session_code,
                    mode=TimerMode.FOCUS.value,
                    status=TimerStatus.IDLE.value,
                    duration=focus_duration,
                    remaining_seconds=focus_duration
                )
                self.repo.save_timer(timer)
            else:
                # Update status if completed
                if timer.status == TimerStatus.RUNNING.value and timer.target_end_time:
                    now = time.time()
                    if now >= timer.target_end_time:
                        timer.status = TimerStatus.COMPLETED.value
                        timer.remaining_seconds = 0
                        timer.target_end_time = None
                        if timer.mode == TimerMode.FOCUS.value:
                            timer.completed_sessions += 1
                        self.repo.save_timer(timer)
            return timer

    def start_timer(self, session_code: str) -> Tuple[bool, str, TimerState]:
        with self._lock:
            timer = self.get_or_create_timer(session_code)
            now = time.time()

            if timer.status == TimerStatus.RUNNING.value:
                return True, "Timer already running", timer

            if timer.status == TimerStatus.COMPLETED.value or timer.remaining_seconds <= 0:
                timer.remaining_seconds = timer.duration

            timer.status = TimerStatus.RUNNING.value
            timer.started_at = now
            timer.target_end_time = now + timer.remaining_seconds
            timer.updated_at = now
            
            saved = self.repo.save_timer(timer)
            return True, "Timer started", saved

    def pause_timer(self, session_code: str) -> Tuple[bool, str, TimerState]:
        with self._lock:
            timer = self.get_or_create_timer(session_code)
            now = time.time()

            if timer.status != TimerStatus.RUNNING.value:
                return True, "Timer not running", timer

            remaining = max(0, int(timer.target_end_time - now)) if timer.target_end_time else timer.remaining_seconds
            timer.status = TimerStatus.PAUSED.value
            timer.remaining_seconds = remaining
            timer.target_end_time = None
            timer.updated_at = now

            saved = self.repo.save_timer(timer)
            return True, "Timer paused", saved

    def resume_timer(self, session_code: str) -> Tuple[bool, str, TimerState]:
        return self.start_timer(session_code)

    def reset_timer(self, session_code: str) -> Tuple[bool, str, TimerState]:
        with self._lock:
            timer = self.get_or_create_timer(session_code)
            now = time.time()

            timer.status = TimerStatus.IDLE.value
            timer.remaining_seconds = timer.duration
            timer.started_at = None
            timer.target_end_time = None
            timer.updated_at = now

            saved = self.repo.save_timer(timer)
            return True, "Timer reset", saved

    def skip_timer(self, session_code: str, settings: Optional[SessionSettings] = None) -> Tuple[bool, str, TimerState]:
        with self._lock:
            timer = self.get_or_create_timer(session_code, settings)
            
            # Rotate modes: FOCUS -> SHORT_BREAK -> FOCUS (or LONG_BREAK every 4 sessions)
            if timer.mode == TimerMode.FOCUS.value:
                if timer.completed_sessions > 0 and timer.completed_sessions % 4 == 0:
                    next_mode = TimerMode.LONG_BREAK.value
                else:
                    next_mode = TimerMode.SHORT_BREAK.value
            else:
                next_mode = TimerMode.FOCUS.value

            return self.change_mode(session_code, next_mode, settings)

    def change_mode(self, session_code: str, new_mode: str, settings: Optional[SessionSettings] = None) -> Tuple[bool, str, TimerState]:
        with self._lock:
            timer = self.get_or_create_timer(session_code, settings)
            if new_mode not in [TimerMode.FOCUS.value, TimerMode.SHORT_BREAK.value, TimerMode.LONG_BREAK.value]:
                return False, "Invalid mode", timer

            duration_mins = 25
            if settings:
                if new_mode == TimerMode.FOCUS.value:
                    duration_mins = settings.focus_duration
                elif new_mode == TimerMode.SHORT_BREAK.value:
                    duration_mins = settings.short_break_duration
                elif new_mode == TimerMode.LONG_BREAK.value:
                    duration_mins = settings.long_break_duration

            duration_secs = duration_mins * 60
            now = time.time()

            timer.mode = new_mode
            timer.status = TimerStatus.IDLE.value
            timer.duration = duration_secs
            timer.remaining_seconds = duration_secs
            timer.started_at = None
            timer.target_end_time = None
            timer.updated_at = now

            saved = self.repo.save_timer(timer)
            return True, f"Mode changed to {new_mode}", saved

    def update_durations_from_settings(self, session_code: str, settings: SessionSettings) -> TimerState:
        with self._lock:
            timer = self.get_or_create_timer(session_code, settings)
            duration_mins = settings.focus_duration
            if timer.mode == TimerMode.SHORT_BREAK.value:
                duration_mins = settings.short_break_duration
            elif timer.mode == TimerMode.LONG_BREAK.value:
                duration_mins = settings.long_break_duration
            
            new_duration_secs = duration_mins * 60
            if timer.duration != new_duration_secs:
                timer.duration = new_duration_secs
                if timer.status == TimerStatus.IDLE.value:
                    timer.remaining_seconds = new_duration_secs
                self.repo.save_timer(timer)
            return timer
