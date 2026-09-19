import time
from app.repositories.memory_repo import MemoryRepository
from app.services.timer_service import TimerService
from app.services.settings_service import SettingsService
from app.utilities.constants import TimerMode, TimerStatus

def test_timer_lifecycle():
    repo = MemoryRepository()
    settings_service = SettingsService(repo)
    timer_service = TimerService(repo)
    room_code = "TEST01"

    settings = settings_service.get_or_create_settings(room_code)
    timer = timer_service.get_or_create_timer(room_code, settings)

    assert timer.status == TimerStatus.IDLE.value
    assert timer.duration == 1500

    # Start
    ok, msg, timer = timer_service.start_timer(room_code)
    assert ok is True
    assert timer.status == TimerStatus.RUNNING.value
    assert timer.target_end_time is not None

    # Pause
    ok, msg, timer = timer_service.pause_timer(room_code)
    assert ok is True
    assert timer.status == TimerStatus.PAUSED.value

    # Change Mode to Short Break
    ok, msg, timer = timer_service.change_mode(room_code, TimerMode.SHORT_BREAK.value, settings)
    assert ok is True
    assert timer.mode == TimerMode.SHORT_BREAK.value
    assert timer.duration == 300
    assert timer.remaining_seconds == 300

    # Reset
    ok, msg, timer = timer_service.reset_timer(room_code)
    assert ok is True
    assert timer.status == TimerStatus.IDLE.value
    assert timer.remaining_seconds == 300
