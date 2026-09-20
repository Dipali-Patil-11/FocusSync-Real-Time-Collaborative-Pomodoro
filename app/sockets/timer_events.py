import uuid
from flask_socketio import emit
from app.utilities.db import get_repository
from app.services.timer_service import TimerService
from app.services.settings_service import SettingsService
from app.utilities.logger import logger

def get_start_notification_payload(mode: str, duration_secs: int) -> dict:
    mode_titles = {
        "FOCUS": ("Focus session started", "Time to focus!"),
        "SHORT_BREAK": ("Short break started", "Take a short break."),
        "LONG_BREAK": ("Long break started", "Enjoy your long break.")
    }
    title, msg = mode_titles.get(mode, ("Timer started", "Session started."))
    return {
        "event_id": str(uuid.uuid4()),
        "mode": mode,
        "title": title,
        "message": msg,
        "duration": duration_secs // 60
    }

def get_complete_notification_payload(mode: str) -> dict:
    mode_titles = {
        "FOCUS": ("Focus session completed", "Your focus session is complete."),
        "SHORT_BREAK": ("Short break completed", "Your short break is complete."),
        "LONG_BREAK": ("Long break completed", "Your long break is complete.")
    }
    title, msg = mode_titles.get(mode, ("Timer completed", "Session completed."))
    return {
        "event_id": str(uuid.uuid4()),
        "mode": mode,
        "title": title,
        "message": msg
    }

def register_timer_events(socketio):

    @socketio.on('timer_start')
    def handle_timer_start(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.start_timer(session_code)
        if success:
            emit('timer_start', {'timer': timer.to_dict(), 'message': msg}, to=session_code)
            notification = get_start_notification_payload(timer.mode, timer.duration)
            emit('timer_started_notification', notification, to=session_code)

    @socketio.on('timer_pause')
    def handle_timer_pause(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.pause_timer(session_code)
        if success:
            emit('timer_pause', {'timer': timer.to_dict(), 'message': msg}, to=session_code)

    @socketio.on('timer_resume')
    def handle_timer_resume(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.resume_timer(session_code)
        if success:
            emit('timer_resume', {'timer': timer.to_dict(), 'message': msg}, to=session_code)
            notification = get_start_notification_payload(timer.mode, timer.duration)
            emit('timer_started_notification', notification, to=session_code)

    @socketio.on('timer_reset')
    def handle_timer_reset(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.reset_timer(session_code)
        if success:
            emit('timer_reset', {'timer': timer.to_dict(), 'message': msg}, to=session_code)

    @socketio.on('timer_skip')
    def handle_timer_skip(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)
        
        settings = settings_service.get_or_create_settings(session_code)
        success, msg, timer = timer_service.skip_timer(session_code, settings)
        if success:
            emit('timer_skip', {'timer': timer.to_dict(), 'message': msg}, to=session_code)

    @socketio.on('timer_change_mode')
    def handle_timer_change_mode(data):
        session_code = data.get('session_code', '').upper()
        new_mode = data.get('mode')
        if not session_code or not new_mode:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        settings = settings_service.get_or_create_settings(session_code)
        success, msg, timer = timer_service.change_mode(session_code, new_mode, settings)
        if success:
            emit('timer_mode_changed', {'timer': timer.to_dict(), 'message': msg}, to=session_code)

    @socketio.on('timer_complete')
    def handle_timer_complete(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        settings = settings_service.get_or_create_settings(session_code)
        success, msg, timer, completed_mode, next_mode, auto_started = timer_service.complete_timer(session_code, settings)

        comp_notification = get_complete_notification_payload(completed_mode)
        emit('timer_completed_notification', comp_notification, to=session_code)

        if auto_started:
            emit('timer_start', {'timer': timer.to_dict(), 'message': f'Next mode ({next_mode}) started automatically'}, to=session_code)
            start_notification = get_start_notification_payload(timer.mode, timer.duration)
            emit('timer_started_notification', start_notification, to=session_code)
        else:
            emit('timer_mode_changed', {'timer': timer.to_dict(), 'message': f'Switched to {next_mode}'}, to=session_code)

    @socketio.on('settings_updated')
    def handle_settings_updated(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        
        focus = data.get('focus_duration', 25)
        short_b = data.get('short_break_duration', 5)
        long_b = data.get('long_break_duration', 15)
        long_b_interval = data.get('long_break_interval', 4)
        auto_start = data.get('auto_start', False)
        sound = data.get('sound_enabled', True)

        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        success, msg, settings = settings_service.update_settings(
            session_code, focus, short_b, long_b, long_b_interval, auto_start, sound
        )
        if not success:
            emit('session_error', {'message': msg})
            return

        timer = timer_service.update_durations_from_settings(session_code, settings)

        emit('settings_updated', {
            'settings': settings.to_dict(),
            'timer': timer.to_dict(),
            'message': 'Settings updated'
        }, to=session_code)
