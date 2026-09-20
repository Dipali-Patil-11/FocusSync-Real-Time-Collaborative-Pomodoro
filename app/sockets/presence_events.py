from flask import request
from flask_socketio import emit
from app.utilities.db import get_repository
from app.services.presence_service import PresenceService
from app.services.session_service import SessionService
from app.utilities.logger import logger

def register_presence_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        logger.info(f"Client disconnected: {sid}")
        repo = get_repository()
        presence_service = PresenceService(repo)
        session_service = SessionService(repo)

        participant = presence_service.set_offline_by_sid(sid)
        if participant:
            session_code = participant.session_code
            state = session_service.get_session_state(session_code)
            pts = state['participants'] if state else []
            emit('presence_update', {
                'participant_token': participant.participant_token,
                'is_online': False,
                'participants': pts,
                'message': f"{participant.username} went offline"
            }, to=session_code)
