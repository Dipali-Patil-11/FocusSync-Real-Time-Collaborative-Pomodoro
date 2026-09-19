from flask import Blueprint, jsonify, request
from app.utilities.db import get_repository, get_db_mode
from app.services.room_service import RoomService

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "FocusSync-Realtime",
        "database_mode": get_db_mode()
    }), 200

@api_bp.route('/rooms/create', methods=['POST'])
def create_room():
    data = request.get_json() or {}
    username = data.get('username')

    repo = get_repository()
    room_service = RoomService(repo)
    success, message, result = room_service.create_room(username)

    if not success:
        return jsonify({"success": False, "message": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 201

@api_bp.route('/rooms/join', methods=['POST'])
def join_room():
    data = request.get_json() or {}
    room_code = data.get('room_code')
    username = data.get('username')
    token = data.get('participant_token')

    repo = get_repository()
    room_service = RoomService(repo)
    success, message, result, status_code = room_service.join_room(room_code, username, token)

    if not success:
        http_code = 404 if status_code == 'NOT_FOUND' else (409 if status_code == 'FULL' else 400)
        return jsonify({
            "success": False,
            "message": message,
            "error_code": status_code
        }), http_code

    return jsonify({"success": True, "message": message, "data": result}), 200

@api_bp.route('/rooms/<room_code>', methods=['GET'])
def get_room_info(room_code):
    repo = get_repository()
    room_service = RoomService(repo)
    state = room_service.get_room_state(room_code.upper())

    if not state:
        return jsonify({"success": False, "message": "Room not found"}), 404

    return jsonify({"success": True, "data": state}), 200
