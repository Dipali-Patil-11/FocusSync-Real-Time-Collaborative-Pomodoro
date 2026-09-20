import uuid
from flask import request
from flask_socketio import join_room, leave_room, emit
from app.utilities.db import get_repository
from app.services.session_service import SessionService
from app.services.presence_service import PresenceService
from app.utilities.logger import logger

def register_session_events(socketio):

    @socketio.on('join_session')
    def handle_join_session(data):
        session_code = data.get('session_code', '').upper()
        username = data.get('username')
        participant_token = data.get('participant_token')

        if not session_code or not username:
            emit('session_error', {'message': 'Session code and username required'})
            return

        repo = get_repository()
        session_service = SessionService(repo)
        presence_service = PresenceService(repo)

        success, message, result, status_code = session_service.join_session(session_code, username, participant_token)

        if not success:
            if status_code == 'FULL':
                emit('session_capacity_reached', {'message': message, 'session_code': session_code})
            else:
                emit('session_error', {'message': message})
            return

        # Join SocketIO room channel using session_code
        join_room(session_code)
        
        # Mark presence online with sid
        p_token = result['participant_token']
        presence_service.set_online(p_token, request.sid)

        # Updated state after presence set
        updated_state = session_service.get_session_state(session_code)

        # Emit session_state to joined client
        emit('session_state', {
            'session_code': session_code,
            'participant_token': p_token,
            'participant': result['participant'],
            'session': updated_state['session'],
            'timer': updated_state['timer'],
            'settings': updated_state['settings'],
            'max_participants': updated_state.get('max_participants', 5),
            'participants': updated_state['participants']
        })

        # Broadcast participant_joined to others in session ONLY (include_self=False)
        emit('participant_joined', {
            'event_id': str(uuid.uuid4()),
            'participant_id': p_token,
            'username': username,
            'session_code': session_code,
            'participant': result['participant'],
            'max_participants': updated_state.get('max_participants', 5),
            'participants': updated_state['participants'],
            'title': f"{username} joined the focus session",
            'message': f"{username} joined the focus session"
        }, to=session_code, include_self=False)

        logger.info(f"Socket {request.sid} ({username}) joined session {session_code}")

    @socketio.on('leave_session')
    def handle_leave_session(data):
        participant_token = data.get('participant_token')
        session_code = data.get('session_code', '').upper()

        if not participant_token:
            return

        repo = get_repository()
        session_service = SessionService(repo)
        participant = repo.get_participant(participant_token)
        username = participant.username if participant else "A participant"

        success, message, s_code = session_service.leave_session(participant_token)

        if success and s_code:
            leave_room(s_code)
            state = session_service.get_session_state(s_code)
            remaining_pts = state['participants'] if state else []
            max_p = state.get('max_participants', 5) if state else 5
            emit('participant_left', {
                'event_id': str(uuid.uuid4()),
                'participant_id': participant_token,
                'username': username,
                'session_code': s_code,
                'max_participants': max_p,
                'participants': remaining_pts,
                'title': f"{username} left the focus session",
                'message': f"{username} left the focus session"
            }, to=s_code)

    @socketio.on('request_sync')
    def handle_request_sync(data):
        session_code = data.get('session_code', '').upper()
        if not session_code:
            return
        repo = get_repository()
        session_service = SessionService(repo)
        state = session_service.get_session_state(session_code)
        if state:
            emit('session_state', state)
