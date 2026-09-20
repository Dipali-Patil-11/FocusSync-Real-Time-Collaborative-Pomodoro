import pytest
from app import create_app, socketio
from app.repositories.memory_repo import MemoryRepository
from app.services.timer_service import TimerService
from app.services.settings_service import SettingsService
from app.utilities.constants import TimerMode, TimerStatus

def test_default_long_break_interval():
    repo = MemoryRepository()
    settings_service = SettingsService(repo)
    settings = settings_service.get_or_create_settings("TEST_DEF")
    assert settings.long_break_interval == 4

def test_pomodoro_cycle_progression_default_interval():
    repo = MemoryRepository()
    settings_service = SettingsService(repo)
    timer_service = TimerService(repo)
    session_code = "TEST_CYCLE"

    settings = settings_service.get_or_create_settings(session_code)
    # Ensure auto_start is False for controlled step-by-step testing
    settings_service.update_settings(session_code, 25, 5, 15, 4, False, True)
    settings = repo.get_settings(session_code)

    # 1. Focus 1 completes -> Short Break (completed_sessions = 1)
    _, _, timer, completed_mode, next_mode, auto_started = timer_service.complete_timer(session_code, settings)
    assert completed_mode == TimerMode.FOCUS.value
    assert next_mode == TimerMode.SHORT_BREAK.value
    assert timer.completed_sessions == 1
    assert timer.status == TimerStatus.IDLE.value

    # 2. Short Break completes -> Focus (completed_sessions remains 1)
    _, _, timer, completed_mode, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert completed_mode == TimerMode.SHORT_BREAK.value
    assert next_mode == TimerMode.FOCUS.value
    assert timer.completed_sessions == 1

    # 3. Focus 2 completes -> Short Break (completed_sessions = 2)
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.SHORT_BREAK.value
    assert timer.completed_sessions == 2

    # 4. Short Break completes -> Focus
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.FOCUS.value

    # 5. Focus 3 completes -> Short Break (completed_sessions = 3)
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.SHORT_BREAK.value
    assert timer.completed_sessions == 3

    # 6. Short Break completes -> Focus
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.FOCUS.value

    # 7. Focus 4 completes -> Long Break (completed_sessions = 4 == long_break_interval)
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.LONG_BREAK.value
    assert timer.completed_sessions == 4

    # 8. Long Break completes -> Focus & counter reset (completed_sessions = 0)
    _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
    assert next_mode == TimerMode.FOCUS.value
    assert timer.completed_sessions == 0

def test_custom_intervals():
    for interval in [2, 3, 5]:
        repo = MemoryRepository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)
        session_code = f"TEST_INT_{interval}"

        settings_service.update_settings(session_code, 25, 5, 15, interval, False, True)
        settings = repo.get_settings(session_code)

        # Complete (interval - 1) focus sessions -> should all trigger SHORT_BREAK
        for i in range(1, interval):
            # Focus completion
            _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
            assert next_mode == TimerMode.SHORT_BREAK.value
            assert timer.completed_sessions == i
            # Short break completion
            _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
            assert next_mode == TimerMode.FOCUS.value

        # The interval-th Focus completion -> MUST trigger LONG_BREAK
        _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
        assert next_mode == TimerMode.LONG_BREAK.value
        assert timer.completed_sessions == interval

        # Long break completion -> resets completed_sessions to 0 & returns to FOCUS
        _, _, timer, _, next_mode, _ = timer_service.complete_timer(session_code, settings)
        assert next_mode == TimerMode.FOCUS.value
        assert timer.completed_sessions == 0

def test_auto_start_on_vs_off():
    repo = MemoryRepository()
    settings_service = SettingsService(repo)
    timer_service = TimerService(repo)
    session_code = "TEST_AUTO"

    # Test Auto Start OFF
    settings_service.update_settings(session_code, 25, 5, 15, 4, False, True)
    settings = repo.get_settings(session_code)
    _, _, timer, _, _, auto_started = timer_service.complete_timer(session_code, settings)
    assert auto_started is False
    assert timer.status == TimerStatus.IDLE.value

    # Test Auto Start ON
    settings_service.update_settings(session_code, 25, 5, 15, 4, True, True)
    settings = repo.get_settings(session_code)
    _, _, timer, _, _, auto_started = timer_service.complete_timer(session_code, settings)
    assert auto_started is True
    assert timer.status == TimerStatus.RUNNING.value
    assert timer.target_end_time is not None

def test_skip_rules():
    repo = MemoryRepository()
    settings_service = SettingsService(repo)
    timer_service = TimerService(repo)
    session_code = "TEST_SKIP"

    settings = settings_service.get_or_create_settings(session_code)

    # 1. Skip Focus session -> moves to SHORT_BREAK without incrementing completed_sessions
    ok, msg, timer = timer_service.skip_timer(session_code, settings)
    assert ok is True
    assert timer.mode == TimerMode.SHORT_BREAK.value
    assert timer.completed_sessions == 0  # Did NOT increment!

    # 2. Skip Short Break -> moves to FOCUS
    ok, msg, timer = timer_service.skip_timer(session_code, settings)
    assert timer.mode == TimerMode.FOCUS.value
    assert timer.completed_sessions == 0

    # Manually set completed_sessions to 4 to test Long Break skip
    timer.completed_sessions = 4
    timer.mode = TimerMode.LONG_BREAK.value
    repo.save_timer(timer)

    # 3. Skip Long Break -> resets completed_sessions = 0 & moves to FOCUS
    ok, msg, timer = timer_service.skip_timer(session_code, settings)
    assert timer.mode == TimerMode.FOCUS.value
    assert timer.completed_sessions == 0

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

def test_multi_client_socket_sync_and_reconnect(app):
    client1 = socketio.test_client(app)
    client2 = socketio.test_client(app)

    with app.test_client() as http_client:
        http_client.get('/api/auth/me')
        csrf_token = http_client.get_cookie('csrf_token').value
        headers = {'X-CSRF-Token': csrf_token}

        rv = http_client.post('/api/sessions/create', json={"username": "User1"}, headers=headers)
        code = rv.get_json()["data"]["session_code"]
        token1 = rv.get_json()["data"]["participant_token"]

        rv2 = http_client.post('/api/sessions/join', json={"session_code": code, "username": "User2"}, headers=headers)
        token2 = rv2.get_json()["data"]["participant_token"]

    # Both clients join
    client1.emit('join_session', {'session_code': code, 'username': 'User1', 'participant_token': token1})
    client2.emit('join_session', {'session_code': code, 'username': 'User2', 'participant_token': token2})

    # Client 1 updates settings (long_break_interval = 3)
    client1.emit('settings_updated', {
        'session_code': code,
        'focus_duration': 25,
        'short_break_duration': 5,
        'long_break_duration': 15,
        'long_break_interval': 3,
        'auto_start': False,
        'sound_enabled': True
    })

    rec2 = client2.get_received()
    settings_events = [e for e in rec2 if e['name'] == 'settings_updated']
    assert len(settings_events) > 0
    assert settings_events[0]['args'][0]['settings']['long_break_interval'] == 3

    # Client 1 emits timer_complete
    client1.emit('timer_complete', {'session_code': code})

    rec2_timer = client2.get_received()
    completed_events = [e for e in rec2_timer if e['name'] == 'timer_completed_notification']
    assert len(completed_events) > 0

    # Reconnect test: client3 joins existing session
    client3 = socketio.test_client(app)
    client3.emit('join_session', {'session_code': code, 'username': 'User1', 'participant_token': token1})

    rec3 = client3.get_received()
    state_event = [e for e in rec3 if e['name'] == 'session_state'][0]
    timer_state = state_event['args'][0]['timer']
    settings_state = state_event['args'][0]['settings']

    assert settings_state['long_break_interval'] == 3
    assert timer_state['completed_sessions'] == 1
