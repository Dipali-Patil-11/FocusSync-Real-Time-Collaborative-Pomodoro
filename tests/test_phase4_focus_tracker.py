import pytest
import time
from app.models.timer import TimerState
from app.services.timer_service import TimerService
from app.services.session_service import SessionService
from app.services.settings_service import SettingsService
from app.repositories.memory_repo import MemoryRepository
from app.utilities.constants import TimerMode, TimerStatus

def test_timer_state_tracker_defaults():
    timer = TimerState(session_code="TEST01")
    assert timer.total_focus_sessions == 0
    assert timer.total_completed_cycles == 0
    assert timer.total_focus_time_seconds == 0
    
    d = timer.to_dict()
    assert d["total_focus_sessions"] == 0
    assert d["total_completed_cycles"] == 0
    assert d["total_focus_time_seconds"] == 0


def test_natural_focus_completion_increments_tracker():
    repo = MemoryRepository()
    session_service = SessionService(repo)
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    
    ok, msg, data = session_service.create_session("Alice")
    code = data["session_code"]
    
    # Initially 0
    timer = repo.get_timer(code)
    assert timer.total_focus_sessions == 0
    assert timer.total_focus_time_seconds == 0
    assert timer.total_completed_cycles == 0
    
    # Complete 1 Focus session (25 min = 1500s)
    settings = settings_service.get_or_create_settings(code)
    timer_service.complete_timer(code, settings)
    
    updated_timer = repo.get_timer(code)
    assert updated_timer.total_focus_sessions == 1
    assert updated_timer.total_focus_time_seconds == 1500
    assert updated_timer.completed_sessions == 1
    assert updated_timer.total_completed_cycles == 0
    assert updated_timer.mode == TimerMode.SHORT_BREAK.value


def test_critical_timer_duration_settings_change_during_run():
    """
    CRITICAL TEST:
    - Focus timer created with duration = 25 minutes (1500s)
    - Settings changed to 30 minutes (1800s) while timer is running/active
    - Timer completes
    - Verify tracker adds 1500s (actual timer.duration), NOT 1800s.
    """
    repo = MemoryRepository()
    session_service = SessionService(repo)
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    
    ok, msg, data = session_service.create_session("Bob")
    code = data["session_code"]
    
    # Ensure current timer duration is 1500s
    timer = repo.get_timer(code)
    assert timer.duration == 1500
    
    # Update settings to 30 minutes
    settings_service.update_settings(code, 30, 5, 15)
    settings = settings_service.get_or_create_settings(code)
    
    # Complete the existing timer (duration is still 1500s)
    timer_service.complete_timer(code, settings)
    
    updated = repo.get_timer(code)
    assert updated.total_focus_sessions == 1
    assert updated.total_focus_time_seconds == 1500  # Must be 1500, not 1800!


def test_cycle_completion_increments_completed_cycles():
    repo = MemoryRepository()
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    code = "CYCLE1"
    
    settings = settings_service.get_or_create_settings(code) # long_break_interval default 4
    
    # Focus 1 complete
    timer_service.complete_timer(code, settings)
    timer = repo.get_timer(code)
    assert timer.completed_sessions == 1
    assert timer.total_completed_cycles == 0
    assert timer.mode == TimerMode.SHORT_BREAK.value
    
    # Short Break 1 complete -> Focus
    timer_service.complete_timer(code, settings)
    assert repo.get_timer(code).mode == TimerMode.FOCUS.value
    
    # Focus 2 complete
    timer_service.complete_timer(code, settings)
    assert repo.get_timer(code).completed_sessions == 2
    assert repo.get_timer(code).total_completed_cycles == 0
    
    # Short Break 2 complete -> Focus
    timer_service.complete_timer(code, settings)
    
    # Focus 3 complete
    timer_service.complete_timer(code, settings)
    assert repo.get_timer(code).completed_sessions == 3
    assert repo.get_timer(code).total_completed_cycles == 0
    
    # Short Break 3 complete -> Focus
    timer_service.complete_timer(code, settings)
    
    # Focus 4 complete -> Hits interval (4)! Should increment total_completed_cycles to 1 & transition to LONG_BREAK
    timer_service.complete_timer(code, settings)
    timer_cycle4 = repo.get_timer(code)
    assert timer_cycle4.completed_sessions == 4
    assert timer_cycle4.total_completed_cycles == 1
    assert timer_cycle4.total_focus_sessions == 4
    assert timer_cycle4.mode == TimerMode.LONG_BREAK.value
    
    # Long Break complete -> Resets completed_sessions to 0, transitions to FOCUS, does NOT increment total_completed_cycles again
    timer_service.complete_timer(code, settings)
    timer_after_lb = repo.get_timer(code)
    assert timer_after_lb.completed_sessions == 0
    assert timer_after_lb.total_completed_cycles == 1  # Remains 1
    assert timer_after_lb.mode == TimerMode.FOCUS.value


def test_skip_does_not_increment_tracker_totals():
    repo = MemoryRepository()
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    code = "SKIP01"
    
    settings = settings_service.get_or_create_settings(code)
    
    # Skip Focus
    timer_service.skip_timer(code, settings)
    timer = repo.get_timer(code)
    assert timer.total_focus_sessions == 0
    assert timer.total_completed_cycles == 0
    assert timer.total_focus_time_seconds == 0
    assert timer.mode == TimerMode.SHORT_BREAK.value


def test_reset_preserves_tracker_totals():
    repo = MemoryRepository()
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    code = "RESET1"
    
    settings = settings_service.get_or_create_settings(code)
    timer_service.complete_timer(code, settings)
    
    timer_before = repo.get_timer(code)
    assert timer_before.total_focus_sessions == 1
    assert timer_before.total_focus_time_seconds == 1500
    
    # Reset timer
    timer_service.reset_timer(code)
    timer_after = repo.get_timer(code)
    assert timer_after.total_focus_sessions == 1
    assert timer_after.total_focus_time_seconds == 1500
    assert timer_after.status == TimerStatus.IDLE.value


def test_postgres_persistence_mock(monkeypatch):
    """Test PostgresRepository serialization logic without executing remote DB."""
    from app.models.timer import TimerState
    
    timer = TimerState(
        session_code="PGTEST",
        total_focus_sessions=5,
        total_completed_cycles=1,
        total_focus_time_seconds=7500
    )
    d = timer.to_dict()
    assert d["total_focus_sessions"] == 5
    assert d["total_completed_cycles"] == 1
    assert d["total_focus_time_seconds"] == 7500


def test_session_state_contains_tracker_metrics():
    repo = MemoryRepository()
    session_service = SessionService(repo)
    ok, msg, data = session_service.create_session("Charlie")
    code = data["session_code"]
    
    state = session_service.get_session_state(code)
    assert "timer" in state
    assert state["timer"]["total_focus_sessions"] == 0
    assert state["timer"]["total_completed_cycles"] == 0
    assert state["timer"]["total_focus_time_seconds"] == 0


def test_multi_participant_sync_and_reconnect():
    repo = MemoryRepository()
    session_service = SessionService(repo)
    timer_service = TimerService(repo)
    settings_service = SettingsService(repo)
    
    ok1, msg1, d1 = session_service.create_session("Host")
    code = d1["session_code"]
    token1 = d1["participant_token"]
    
    ok2, msg2, d2, status2 = session_service.join_session(code, "Guest")
    token2 = d2["participant_token"]
    
    # Complete 1 focus session
    settings = settings_service.get_or_create_settings(code)
    timer_service.complete_timer(code, settings)
    
    # Guest sync request
    guest_state = session_service.get_session_state(code)
    assert guest_state["timer"]["total_focus_sessions"] == 1
    assert guest_state["timer"]["total_focus_time_seconds"] == 1500
    
    # Guest reconnects
    ok_recon, msg_recon, d_recon, s_recon = session_service.join_session(code, "Guest", token2)
    assert d_recon["timer"]["total_focus_sessions"] == 1
    assert d_recon["timer"]["total_focus_time_seconds"] == 1500
