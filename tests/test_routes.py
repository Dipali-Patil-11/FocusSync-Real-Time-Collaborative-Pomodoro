import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def get_csrf_headers(client):
    client.get('/api/auth/me')
    cookie = client.get_cookie('csrf_token')
    token = cookie.value if cookie else ''
    return {'X-CSRF-Token': token}

def test_landing_page(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"FocusSync" in rv.data
    assert b"Focus together." in rv.data

def test_health_endpoint(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data["status"] == "healthy"
    assert "database_mode" in json_data

def test_create_and_join_session_api(client):
    headers = get_csrf_headers(client)

    # Create
    rv = client.post('/api/sessions/create', json={"username": "Alice"}, headers=headers)
    assert rv.status_code == 201
    res = rv.get_json()
    assert res["success"] is True
    code = res["data"]["session_code"]

    # Join participants 2, 3, 4, 5 -> 200 OK
    for i in range(2, 6):
        rv_i = client.post('/api/sessions/join', json={"session_code": code, "username": f"User{i}"}, headers=headers)
        assert rv_i.status_code == 200
        assert rv_i.get_json()["success"] is True

    # Join 6th participant -> 409 FULL
    rv6 = client.post('/api/sessions/join', json={"session_code": code, "username": "User6"}, headers=headers)
    assert rv6.status_code == 409
    assert rv6.get_json()["error_code"] == "FULL"
