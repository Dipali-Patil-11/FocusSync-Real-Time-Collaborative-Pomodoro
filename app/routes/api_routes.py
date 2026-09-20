import secrets
from flask import Blueprint, jsonify, request, session, current_app
from app.utilities.db import get_repository, get_db_mode
from app.services.session_service import SessionService
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

@api_bp.before_request
def check_csrf():
    # Enforce Double-Submit Cookie CSRF for state-changing HTTP endpoints
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        header_token = request.headers.get('X-CSRF-Token')
        data_token = None
        if request.is_json and request.get_json(silent=True):
            data_token = request.get_json(silent=True).get('csrf_token')
        
        client_token = header_token or data_token
        cookie_token = request.cookies.get('csrf_token')

        if not cookie_token or not client_token or not secrets.compare_digest(client_token, cookie_token):
            return jsonify({
                "success": False,
                "message": "CSRF validation failed: missing or invalid CSRF token"
            }), 403

@api_bp.after_request
def set_csrf_cookie(response):
    token = get_csrf_token()
    response.set_cookie('csrf_token', token, httponly=False, samesite='Lax')
    return response

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "FocusSync-Realtime",
        "database_mode": get_db_mode()
    }), 200

# AUTH ENDPOINTS
@api_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    repo = get_repository()
    auth_service = AuthService(repo)
    success, message, user = auth_service.register_user(username, email, password)

    if not success:
        return jsonify({"success": False, "message": message}), 400

    session['user_id'] = user.user_id
    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "user": user.to_dict()
        }
    }), 201

@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username_or_email = data.get('username_or_email') or data.get('username') or data.get('email')
    password = data.get('password')

    repo = get_repository()
    auth_service = AuthService(repo)
    success, message, user = auth_service.login_user(username_or_email, password)

    if not success:
        return jsonify({"success": False, "message": message}), 401

    session['user_id'] = user.user_id
    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "user": user.to_dict()
        }
    }), 200

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    user_id = session.pop('user_id', None)
    if user_id:
        repo = get_repository()
        affected_codes = repo.clear_user_id_from_participants(user_id)
        from app.services.timer_service import TimerService
        timer_service = TimerService(repo)
        for code in affected_codes:
            timer_service.remove_user_from_run(code, user_id)
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@api_bp.route('/auth/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    csrf_tok = get_csrf_token()
    if not user_id:
        return jsonify({
            "success": True,
            "data": {
                "authenticated": False,
                "user": None,
                "csrf_token": csrf_tok
            }
        }), 200

    repo = get_repository()
    auth_service = AuthService(repo)
    user = auth_service.get_user_by_id(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({
            "success": True,
            "data": {
                "authenticated": False,
                "user": None,
                "csrf_token": csrf_tok
            }
        }), 200

    return jsonify({
        "success": True,
        "data": {
            "authenticated": True,
            "user": user.to_dict(),
            "csrf_token": csrf_tok
        }
    }), 200

# USER HISTORY & DASHBOARD
@api_bp.route('/user/history', methods=['GET'])
def get_user_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    repo = get_repository()
    history_service = HistoryService(repo)
    history = history_service.get_user_history(user_id, limit=limit, offset=offset)

    return jsonify({
        "success": True,
        "data": {
            "history": history,
            "limit": limit,
            "offset": offset
        }
    }), 200

@api_bp.route('/user/dashboard', methods=['GET'])
def get_user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    repo = get_repository()
    history_service = HistoryService(repo)
    dashboard_data = history_service.get_user_dashboard(user_id)

    return jsonify({
        "success": True,
        "data": dashboard_data
    }), 200

# SESSIONS ENDPOINTS
@api_bp.route('/sessions/create', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    username = data.get('username')
    user_id = session.get('user_id')

    repo = get_repository()
    session_service = SessionService(repo)
    success, message, result = session_service.create_session(username, user_id=user_id)

    if not success:
        return jsonify({"success": False, "message": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 201

@api_bp.route('/sessions/join', methods=['POST'])
def join_session():
    data = request.get_json() or {}
    session_code = data.get('session_code')
    username = data.get('username')
    token = data.get('participant_token')
    user_id = session.get('user_id')

    repo = get_repository()
    session_service = SessionService(repo)
    success, message, result, status_code = session_service.join_session(
        session_code, username, token, user_id=user_id
    )

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

