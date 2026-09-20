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
                # Check if running timer has expired naturally
                if timer.status == TimerStatus.RUNNING.value and timer.target_end_time:
                    now = time.time()
                    if now >= timer.target_end_time:
                        self.complete_timer(session_code, settings)
                        timer = self.repo.get_timer(session_code)
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

    def complete_timer(self, session_code: str, settings: Optional[SessionSettings] = None) -> Tuple[bool, str, TimerState, str, str, bool]:
        """
        Authoritative timer completion logic.
        Returns (success, message, timer_state, completed_mode, next_mode, auto_started).
        """
        with self._lock:
            if not settings:
                from app.services.settings_service import SettingsService
                settings = SettingsService(self.repo).get_or_create_settings(session_code)

            timer = self.repo.get_timer(session_code)
            if not timer:
                timer = self.get_or_create_timer(session_code, settings)

            completed_mode = timer.mode
            interval = settings.long_break_interval if settings else 4

            # Determine next mode & update completed_sessions count and tracker metrics
            if completed_mode == TimerMode.FOCUS.value:
                timer.completed_sessions += 1
                timer.total_focus_sessions += 1
                timer.total_focus_time_seconds += timer.duration
                if timer.completed_sessions == interval:
                    timer.total_completed_cycles += 1
                    next_mode = TimerMode.LONG_BREAK.value
                else:
                    next_mode = TimerMode.SHORT_BREAK.value
            elif completed_mode == TimerMode.SHORT_BREAK.value:
                next_mode = TimerMode.FOCUS.value
            elif completed_mode == TimerMode.LONG_BREAK.value:
                timer.completed_sessions = 0  # Reset cycle counter after Long Break
                next_mode = TimerMode.FOCUS.value
            else:
                next_mode = TimerMode.FOCUS.value

            # Determine new mode duration
            duration_mins = settings.focus_duration
            if next_mode == TimerMode.SHORT_BREAK.value:
                duration_mins = settings.short_break_duration
            elif next_mode == TimerMode.LONG_BREAK.value:
                duration_mins = settings.long_break_duration
            duration_secs = duration_mins * 60

            now = time.time()
            timer.mode = next_mode
            timer.duration = duration_secs
            timer.updated_at = now

            auto_started = False
            if settings and settings.auto_start:
                timer.status = TimerStatus.RUNNING.value
                timer.started_at = now
                timer.target_end_time = now + duration_secs
                timer.remaining_seconds = duration_secs
                auto_started = True
            else:
                timer.status = TimerStatus.IDLE.value
                timer.started_at = None
                timer.target_end_time = None
                timer.remaining_seconds = duration_secs

            saved = self.repo.save_timer(timer)
            return True, f"Timer completed. Transitioned to {next_mode}", saved, completed_mode, next_mode, auto_started

    def skip_timer(self, session_code: str, settings: Optional[SessionSettings] = None) -> Tuple[bool, str, TimerState]:
        """
        Skip logic:
        - Skipping FOCUS moves to SHORT_BREAK without incrementing completed_sessions (never triggers Long Break).
        - Skipping SHORT_BREAK moves to FOCUS.
        - Skipping LONG_BREAK resets completed_sessions to 0 and moves to FOCUS.
        """
        with self._lock:
            if not settings:
                from app.services.settings_service import SettingsService
                settings = SettingsService(self.repo).get_or_create_settings(session_code)

            timer = self.get_or_create_timer(session_code, settings)

            if timer.mode == TimerMode.FOCUS.value:
                next_mode = TimerMode.SHORT_BREAK.value
                # Do NOT increment completed_sessions on skip
            elif timer.mode == TimerMode.SHORT_BREAK.value:
                next_mode = TimerMode.FOCUS.value
            elif timer.mode == TimerMode.LONG_BREAK.value:
                timer.completed_sessions = 0  # Reset cycle counter on Long Break skip
                next_mode = TimerMode.FOCUS.value
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
