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
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.start_timer(room_code)
        if success:
            emit('timer_start', {'timer': timer.to_dict(), 'message': msg}, to=room_code)
            notification = get_start_notification_payload(timer.mode, timer.duration)
            emit('timer_started_notification', notification, to=room_code)

    @socketio.on('timer_pause')
    def handle_timer_pause(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.pause_timer(room_code)
        if success:
            emit('timer_pause', {'timer': timer.to_dict(), 'message': msg}, to=room_code)

    @socketio.on('timer_resume')
    def handle_timer_resume(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.resume_timer(room_code)
        if success:
            emit('timer_resume', {'timer': timer.to_dict(), 'message': msg}, to=room_code)
            notification = get_start_notification_payload(timer.mode, timer.duration)
            emit('timer_started_notification', notification, to=room_code)

    @socketio.on('timer_reset')
    def handle_timer_reset(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        timer_service = TimerService(repo)
        success, msg, timer = timer_service.reset_timer(room_code)
        if success:
            emit('timer_reset', {'timer': timer.to_dict(), 'message': msg}, to=room_code)

    @socketio.on('timer_skip')
    def handle_timer_skip(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)
        
        settings = settings_service.get_or_create_settings(room_code)
        success, msg, timer = timer_service.skip_timer(room_code, settings)
        if success:
            emit('timer_skip', {'timer': timer.to_dict(), 'message': msg}, to=room_code)

    @socketio.on('timer_change_mode')
    def handle_timer_change_mode(data):
        room_code = data.get('room_code', '').upper()
        new_mode = data.get('mode')
        if not room_code or not new_mode:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        settings = settings_service.get_or_create_settings(room_code)
        success, msg, timer = timer_service.change_mode(room_code, new_mode, settings)
        if success:
            emit('timer_mode_changed', {'timer': timer.to_dict(), 'message': msg}, to=room_code)

    @socketio.on('timer_complete')
    def handle_timer_complete(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        settings = settings_service.get_or_create_settings(room_code)
        timer = timer_service.get_or_create_timer(room_code, settings)

        if timer.status != 'COMPLETED':
            timer.status = 'COMPLETED'
            timer.remaining_seconds = 0
            timer.target_end_time = None
            if timer.mode == 'FOCUS':
                timer.completed_sessions += 1
            repo.save_timer(timer)

        emit('timer_completed', {'timer': timer.to_dict()}, to=room_code)
        comp_notification = get_complete_notification_payload(timer.mode)
        emit('timer_completed_notification', comp_notification, to=room_code)

        # Handle auto-start next session if enabled in room settings
        if settings.auto_start:
            success_skip, _, next_timer = timer_service.skip_timer(room_code, settings)
            if success_skip:
                success_start, msg_start, started_timer = timer_service.start_timer(room_code)
                if success_start:
                    emit('timer_start', {'timer': started_timer.to_dict(), 'message': msg_start}, to=room_code)
                    start_notification = get_start_notification_payload(started_timer.mode, started_timer.duration)
                    emit('timer_started_notification', start_notification, to=room_code)

    @socketio.on('settings_updated')
    def handle_settings_updated(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        
        focus = data.get('focus_duration', 25)
        short_b = data.get('short_break_duration', 5)
        long_b = data.get('long_break_duration', 15)
        auto_start = data.get('auto_start', False)
        sound = data.get('sound_enabled', True)

        repo = get_repository()
        settings_service = SettingsService(repo)
        timer_service = TimerService(repo)

        success, msg, settings = settings_service.update_settings(room_code, focus, short_b, long_b, auto_start, sound)
        if not success:
            emit('room_error', {'message': msg})
            return

        # Update current timer state based on new duration settings
        timer = timer_service.update_durations_from_settings(room_code, settings)

        emit('settings_updated', {
            'settings': settings.to_dict(),
            'timer': timer.to_dict(),
            'message': 'Settings updated'
        }, to=room_code)

