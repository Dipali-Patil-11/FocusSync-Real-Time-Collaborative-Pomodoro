import pytest
from app import create_app, socketio

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def socket_client(app):
    client = socketio.test_client(app)
    return client

def test_socket_join_and_timer_events(app, socket_client):
    assert socket_client.is_connected()

    # Create session via REST first
    with app.test_client() as http_client:
        http_client.get('/api/auth/me')
        csrf_token = http_client.get_cookie('csrf_token').value
        rv = http_client.post('/api/sessions/create', json={"username": "Alice"}, headers={'X-CSRF-Token': csrf_token})
        code = rv.get_json()["data"]["session_code"]
        token = rv.get_json()["data"]["participant_token"]

    # Join session via socket
    socket_client.emit('join_session', {
        'session_code': code,
        'username': 'Alice',
        'participant_token': token
    })

    received = socket_client.get_received()
    event_names = [e['name'] for e in received]
    assert 'session_state' in event_names

    # Emit timer start
    socket_client.emit('timer_start', {'session_code': code})
    received_after_start = socket_client.get_received()
    start_events = [e['name'] for e in received_after_start]
    assert 'timer_start' in start_events
