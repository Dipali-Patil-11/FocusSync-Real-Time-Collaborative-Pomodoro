import uuid
from flask import request
from flask_socketio import join_room, leave_room, emit
from app.utilities.db import get_repository
from app.services.room_service import RoomService
from app.services.presence_service import PresenceService
from app.utilities.logger import logger

def register_room_events(socketio):

    @socketio.on('join_room')
    def handle_join_room(data):
        room_code = data.get('room_code', '').upper()
        username = data.get('username')
        participant_token = data.get('participant_token')

        if not room_code or not username:
            emit('room_error', {'message': 'Room code and username required'})
            return

        repo = get_repository()
        room_service = RoomService(repo)
        presence_service = PresenceService(repo)

        success, message, result, status_code = room_service.join_room(room_code, username, participant_token)

        if not success:
            if status_code == 'FULL':
                emit('room_full', {'message': message, 'room_code': room_code})
            else:
                emit('room_error', {'message': message})
            return

        # Join SocketIO room channel
        join_room(room_code)
        
        # Mark presence online with sid
        p_token = result['participant_token']
        presence_service.set_online(p_token, request.sid)

        # Updated state after presence set
        updated_state = room_service.get_room_state(room_code)

        # Emit room_state to joined client
        emit('room_state', {
            'room_code': room_code,
            'participant_token': p_token,
            'participant': result['participant'],
            'room': updated_state['room'],
            'timer': updated_state['timer'],
            'settings': updated_state['settings'],
            'participants': updated_state['participants']
        })

        # Broadcast participant_joined to others in room ONLY (include_self=False)
        emit('participant_joined', {
            'event_id': str(uuid.uuid4()),
            'participant_id': p_token,
            'username': username,
            'room_code': room_code,
            'participant': result['participant'],
            'participants': updated_state['participants'],
            'title': f"{username} joined the focus room",
            'message': f"{username} joined the focus room"
        }, to=room_code, include_self=False)

        logger.info(f"Socket {request.sid} ({username}) joined room {room_code}")

    @socketio.on('leave_room')
    def handle_leave_room(data):
        participant_token = data.get('participant_token')
        room_code = data.get('room_code', '').upper()

        if not participant_token:
            return

        repo = get_repository()
        room_service = RoomService(repo)
        participant = repo.get_participant(participant_token)
        username = participant.username if participant else "A participant"

        success, message, r_code = room_service.leave_room(participant_token)

        if success and r_code:
            leave_room(r_code)
            state = room_service.get_room_state(r_code)
            remaining_pts = state['participants'] if state else []
            emit('participant_left', {
                'event_id': str(uuid.uuid4()),
                'participant_id': participant_token,
                'username': username,
                'room_code': r_code,
                'participants': remaining_pts,
                'title': f"{username} left the focus room",
                'message': f"{username} left the focus room"
            }, to=r_code)

    @socketio.on('request_sync')
    def handle_request_sync(data):
        room_code = data.get('room_code', '').upper()
        if not room_code:
            return
        repo = get_repository()
        room_service = RoomService(repo)
        state = room_service.get_room_state(room_code)
        if state:
            emit('room_state', state)

