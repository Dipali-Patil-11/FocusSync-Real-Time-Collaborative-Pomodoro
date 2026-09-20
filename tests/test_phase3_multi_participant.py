import time
import pytest
from app import create_app, socketio
from app.repositories.memory_repo import MemoryRepository
from app.services.session_service import SessionService
from app.utilities.constants import MAX_PARTICIPANTS

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_five_participant_capacity_and_rejection(client):
    """
    Test capacity scaling from 1 to 5 participants and 6th rejection.
    """
    # 1. Create session as User 1
    rv = client.post('/api/sessions/create', json={"username": "User 1"})
    assert rv.status_code == 201
    code = rv.get_json()["data"]["session_code"]

    # 2. Join Users 2, 3, 4, 5 -> PASS
    tokens = [rv.get_json()["data"]["participant_token"]]
    for i in range(2, 6):
        rv_i = client.post('/api/sessions/join', json={"session_code": code, "username": f"User {i}"})
        assert rv_i.status_code == 200
        data = rv_i.get_json()["data"]
        assert data["participant"]["slot"] == i
        assert len(data["participants"]) == i
        tokens.append(data["participant_token"])

    # 3. Join User 6 -> REJECTED (409 FULL)
    rv6 = client.post('/api/sessions/join', json={"session_code": code, "username": "User 6"})
    assert rv6.status_code == 409
    assert rv6.get_json()["error_code"] == "FULL"

def test_slot_recycling(app):
    """
    Test slot recycling: Participant 3 leaves, Participant 6 joins and receives freed Slot 3.
    """
    repo = MemoryRepository()
    service = SessionService(repo)

    # Create & Join 5 users
    ok1, _, res1 = service.create_session("User 1")
    code = res1["session_code"]
    
    tokens = [res1["participant_token"]]
    for i in range(2, 6):
        ok_i, _, res_i, _ = service.join_session(code, f"User {i}")
        assert ok_i is True
        tokens.append(res_i["participant_token"])

    # Verify 6th rejected
    ok6, msg6, _, status6 = service.join_session(code, "User 6")
    assert ok6 is False
    assert status6 == "FULL"

    # User 3 leaves (token at index 2)
    user3_token = tokens[2]
    ok_leave, _, _ = service.leave_session(user3_token)
    assert ok_leave is True

    # User 6 joins now -> Must claim freed slot 3
    ok6_new, _, res6_new, status6_new = service.join_session(code, "User 6 New")
    assert ok6_new is True
    assert status6_new == "OK"
    assert res6_new["participant"]["slot"] == 3

def test_five_client_socket_sync_and_presence(app):
    """
    Verify 5 connected Socket.IO clients receive presence broadcasts & timer sync events.
    """
    flask_client = app.test_client()

    # Create session
    rv = flask_client.post('/api/sessions/create', json={"username": "Owner"})
    assert rv.status_code == 201
    code = rv.get_json()["data"]["session_code"]
    token1 = rv.get_json()["data"]["participant_token"]

    tokens = [token1]
    for i in range(2, 6):
        r = flask_client.post('/api/sessions/join', json={"session_code": code, "username": f"User{i}"})
        assert r.status_code == 200
        tokens.append(r.get_json()["data"]["participant_token"])

    # Connect 5 Socket.IO clients
    clients = []
    for i in range(5):
        s_client = socketio.test_client(app, flask_test_client=flask_client)
        s_client.emit('join_session', {
            'session_code': code,
            'username': f"User{i+1}",
            'participant_token': tokens[i]
        })
        time.sleep(0.05)
        clients.append(s_client)

    # Verify client 1 received participant_joined events for subsequent joiners
    received_by_c1 = clients[0].get_received()
    joined_events = [e for e in received_by_c1 if e['name'] == 'participant_joined']
    assert len(joined_events) >= 1

    # Client 3 triggers timer start
    clients[2].emit('timer_start', {'session_code': code})
    time.sleep(0.1)

    # Verify all 5 clients received timer update / notification
    for idx, c in enumerate(clients):
        events = c.get_received()
        start_events = [e for e in events if e['name'] in ('timer_start', 'timer_started_notification', 'session_state')]
        assert len(start_events) > 0, f"Client {idx+1} did not receive timer start sync"

    # Clean disconnect all
    for c in clients:
        c.disconnect()
