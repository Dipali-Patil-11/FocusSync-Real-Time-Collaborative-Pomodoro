import pytest
from app import create_app
from app.repositories.memory_repo import MemoryRepository
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.services.timer_service import TimerService
from app.services.history_service import HistoryService
from app.utilities.constants import TimerMode, TimerStatus

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture
def repo():
    return MemoryRepository()

# ==========================================
# 1. AUTHENTICATION TESTS
# ==========================================

def test_auth_registration(repo):
    auth_service = AuthService(repo)
    success, msg, user = auth_service.register_user("alice", "alice@example.com", "password123")
    assert success is True
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password_hash != "password123"
    assert "password123" not in user.password_hash

def test_auth_duplicate_email(repo):
    auth_service = AuthService(repo)
    auth_service.register_user("alice", "alice@example.com", "password123")
    success, msg, user = auth_service.register_user("alice2", "alice@example.com", "password456")
    assert success is False
    assert "email" in msg.lower()

def test_auth_duplicate_username(repo):
    auth_service = AuthService(repo)
    auth_service.register_user("alice", "alice@example.com", "password123")
    success, msg, user = auth_service.register_user("alice", "alice2@example.com", "password456")
    assert success is False
    assert "username" in msg.lower()

def test_auth_password_hashing(repo):
    auth_service = AuthService(repo)
    _, _, user = auth_service.register_user("bob", "bob@example.com", "securepass")
    assert auth_service.verify_password(user.password_hash, "securepass") is True
    assert auth_service.verify_password(user.password_hash, "wrongpass") is False

def test_auth_login_and_wrong_password(repo):
    auth_service = AuthService(repo)
    auth_service.register_user("charlie", "charlie@example.com", "pass123")
    
    # Correct login
    success, msg, user = auth_service.login_user("charlie", "pass123")
    assert success is True
    assert user.username == "charlie"

    # Wrong password
    success, msg, user = auth_service.login_user("charlie", "wrong")
    assert success is False
    assert user is None

def test_auth_http_endpoints_and_session_persistence(client):
    # Fetch CSRF cookie first via GET /api/auth/me
    res = client.get('/api/auth/me')
    assert res.status_code == 200
    csrf_token = client.get_cookie('csrf_token').value
    assert csrf_token is not None

    headers = {'X-CSRF-Token': csrf_token}

    # Register
    reg_res = client.post('/api/auth/register', json={
        'username': 'dave',
        'email': 'dave@example.com',
        'password': 'password123'
    }, headers=headers)
    assert reg_res.status_code == 201
    assert reg_res.get_json()['success'] is True

    # Get /me authenticated
    me_res = client.get('/api/auth/me')
    assert me_res.status_code == 200
    me_data = me_res.get_json()['data']
    assert me_data['authenticated'] is True
    assert me_data['user']['username'] == 'dave'

    # Logout
    logout_res = client.post('/api/auth/logout', headers=headers)
    assert logout_res.status_code == 200

    # Get /me logged out
    me_res2 = client.get('/api/auth/me')
    assert me_res2.get_json()['data']['authenticated'] is False

    # Login
    login_res = client.post('/api/auth/login', json={
        'username_or_email': 'dave',
        'password': 'password123'
    }, headers=headers)
    assert login_res.status_code == 200
    assert login_res.get_json()['data']['user']['username'] == 'dave'

# ==========================================
# 2. SECURITY & STRICT CSRF TESTS
# ==========================================

def test_security_password_hash_never_exposed(client):
    res = client.get('/api/auth/me')
    csrf_token = client.get_cookie('csrf_token').value
    headers = {'X-CSRF-Token': csrf_token}

    client.post('/api/auth/register', json={
        'username': 'eve',
        'email': 'eve@example.com',
        'password': 'secretpassword'
    }, headers=headers)

    me = client.get('/api/auth/me').get_json()['data']['user']
    assert 'password_hash' not in me

def test_strict_double_submit_csrf_protection(client):
    # 1. GET request sets initial CSRF cookie
    client.get('/api/auth/me')
    cookie_token = client.get_cookie('csrf_token').value
    assert cookie_token is not None

    # 2. Missing header token -> 403
    res1 = client.post('/api/auth/register', json={'username': 'u1', 'email': 'u1@ex.com', 'password': 'pass123'})
    assert res1.status_code == 403

    # 3. Mismatched header vs cookie -> 403
    res2 = client.post('/api/auth/register', json={'username': 'u1', 'email': 'u1@ex.com', 'password': 'pass123'}, headers={'X-CSRF-Token': 'wrong_token'})
    assert res2.status_code == 403

    # 4. Matching header and cookie -> 201
    res3 = client.post('/api/auth/register', json={'username': 'u1', 'email': 'u1@ex.com', 'password': 'pass123'}, headers={'X-CSRF-Token': cookie_token})
    assert res3.status_code == 201

# ==========================================
# 3. PARTICIPANTS & COEXISTENCE TESTS
# ==========================================

def test_participant_user_id_association_and_coexistence(repo):
    session_service = SessionService(repo)

    # Auth user creates session
    success, _, data = session_service.create_session("AliceCreator", user_id="user_alice")
    assert success is True
    session_code = data['session_code']
    assert data['session']['creator_user_id'] == "user_alice"
    assert data['session']['session_id'] is not None
    assert data['participant']['user_id'] == "user_alice"

    # Guest joins session
    ok_g, _, g_data, _ = session_service.join_session(session_code, "GuestBob", user_id=None)
    assert ok_g is True
    assert g_data['participant']['user_id'] is None

    # Auth user joins session
    ok_u, _, u_data, _ = session_service.join_session(session_code, "AuthCharlie", user_id="user_charlie")
    assert ok_u is True
    assert u_data['participant']['user_id'] == "user_charlie"

    parts = repo.get_participants_by_session(session_code)
    assert len(parts) == 3

def test_participant_capacity_limit(repo):
    session_service = SessionService(repo)
    _, _, data = session_service.create_session("User1", user_id="u1")
    code = data['session_code']

    for i in range(2, 6):
        ok, _, _, _ = session_service.join_session(code, f"User{i}")
        assert ok is True

    ok6, msg6, _, status6 = session_service.join_session(code, "User6")
    assert ok6 is False
    assert status6 == 'FULL'

# ==========================================
# 4. IMMUTABLE SESSION IDENTITY & REUSE TESTS
# ==========================================

def test_session_id_uniqueness(repo):
    session_service = SessionService(repo)
    _, _, s1 = session_service.create_session("User1", user_id="u1")
    _, _, s2 = session_service.create_session("User1", user_id="u1")
    assert s1['session']['session_id'] != s2['session']['session_id']

def test_historical_session_code_reuse_does_not_merge_history(repo):
    session_service = SessionService(repo)
    timer_service = TimerService(repo)
    history_service = HistoryService(repo)

    # 1. Create first session (Session A)
    _, _, s1 = session_service.create_session("User1", user_id="u1")
    code1 = s1['session_code']
    id1 = s1['session']['session_id']
    token1 = s1['participant_token']

    timer_service.start_timer(code1)
    timer_service.complete_timer(code1)
    session_service.leave_session(token1)

    # 2. Simulate room code reuse with a second session (Session B) having SAME session_code but DIFFERENT session_id
    from app.models.session import Session
    s2_obj = Session(session_code=code1, creator_token="token2", creator_user_id="u1")
    repo.create_session(s2_obj)
    id2 = s2_obj.session_id
    history_service.record_session_join("u1", code1, id2, role="CREATOR")

    timer_service.start_timer(code1)
    timer_service.complete_timer(code1)

    # 3. Verify User 1 has TWO separate history records
    u1_hist = history_service.get_user_history("u1")
    assert len(u1_hist) == 2
    ids = {h['session_id'] for h in u1_hist}
    assert ids == {id1, id2}

# ==========================================
# 5. PER-USER CYCLE ATTRIBUTION TESTS
# ==========================================

def test_per_user_cycle_attribution_late_joiner(repo):
    session_service = SessionService(repo)
    timer_service = TimerService(repo)
    history_service = HistoryService(repo)

    # User A creates session
    _, _, data = session_service.create_session("UserA", user_id="u_a")
    code = data['session_code']
    id_a = data['session']['session_id']

    # User A completes 3 Focus sessions
    for _ in range(3):
        timer_service.start_timer(code)
        timer_service.complete_timer(code)
        timer_service.change_mode(code, TimerMode.FOCUS.value)

    # User B joins for Focus 4
    session_service.join_session(code, "UserB", user_id="u_b")

    # Focus 4 starts and completes (completing room cycle 4/4)
    timer_service.start_timer(code)
    timer_service.complete_timer(code)

    hist_a = history_service.get_user_history("u_a")[0]
    hist_b = history_service.get_user_history("u_b")[0]

    # User A completed 4 Focus sessions -> 1 cycle
    assert hist_a['focus_sessions_completed'] == 4
    assert hist_a['cycles_completed'] == 1

    # User B completed 1 Focus session -> 0 cycles (no false cycle credit!)
    assert hist_b['focus_sessions_completed'] == 1
    assert hist_b['cycles_completed'] == 0

# ==========================================
# 6. LOGOUT & ACTIVE SOCKET IDENTITY TESTS
# ==========================================

def test_logout_removes_active_identity_and_attribution(client):
    # 1. Login user
    client.get('/api/auth/me')
    csrf_token = client.get_cookie('csrf_token').value
    headers = {'X-CSRF-Token': csrf_token}

    client.post('/api/auth/register', json={'username': 'LoggedInUser', 'email': 'in@ex.com', 'password': 'password123'}, headers=headers)
    me_res = client.get('/api/auth/me')
    user_id = me_res.get_json()['data']['user']['user_id']

    # 2. User creates session
    c_res = client.post('/api/sessions/create', json={'username': 'LoggedInUser'}, headers=headers)
    code = c_res.get_json()['data']['session_code']

    repo = client.application.config['REPOSITORY_INSTANCE'] if 'REPOSITORY_INSTANCE' in client.application.config else None
    from app.utilities.db import get_repository
    repo = get_repository()

    timer_service = TimerService(repo)
    # Start timer (snapshots user_id)
    timer_service.start_timer(code)
    assert user_id in TimerService._active_run_participants[code]

    # 3. User logs out via HTTP
    logout_res = client.post('/api/auth/logout', headers=headers)
    assert logout_res.status_code == 200

    # 4. Verify user_id converted to None on participant
    pts = repo.get_participants_by_session(code)
    assert pts[0].user_id is None

    # 5. Verify user_id removed from timer attribution snapshot
    assert user_id not in TimerService._active_run_participants.get(code, set())

    # 6. Complete timer -> user gets NO history credit
    timer_service.complete_timer(code)
    from app.services.history_service import HistoryService
    hist = HistoryService(repo).get_user_history(user_id)
    # Only room join record exists, 0 focus completed
    assert hist[0]['focus_sessions_completed'] == 0
