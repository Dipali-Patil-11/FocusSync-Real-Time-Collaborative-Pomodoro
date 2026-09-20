from flask import Blueprint, jsonify, request
from app.utilities.db import get_repository, get_db_mode
from app.services.session_service import SessionService

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "FocusSync-Realtime",
        "database_mode": get_db_mode()
    }), 200

@api_bp.route('/sessions/create', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    username = data.get('username')

    repo = get_repository()
    session_service = SessionService(repo)
    success, message, result = session_service.create_session(username)

    if not success:
        return jsonify({"success": False, "message": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 201

@api_bp.route('/sessions/join', methods=['POST'])
def join_session():
    data = request.get_json() or {}
    session_code = data.get('session_code')
    username = data.get('username')
    token = data.get('participant_token')

    repo = get_repository()
    session_service = SessionService(repo)
    success, message, result, status_code = session_service.join_session(session_code, username, token)

    if not success:
        http_code = 404 if status_code == 'NOT_FOUND' else (409 if status_code == 'FULL' else 400)
        return jsonify({
            "success": False,
            "message": message,
            "error_code": status_code
        }), http_code

    return jsonify({"success": True, "message": message, "data": result}), 200

@api_bp.route('/sessions/<session_code>', methods=['GET'])
def get_session_info(session_code):
    repo = get_repository()
    session_service = SessionService(repo)
    state = session_service.get_session_state(session_code.upper())

    if not state:
        return jsonify({"success": False, "message": "Session not found"}), 404

    return jsonify({"success": True, "data": state}), 200
