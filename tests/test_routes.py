import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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

def test_create_and_join_room_api(client):
    # Create
    rv = client.post('/api/rooms/create', json={"username": "Alice"})
    assert rv.status_code == 201
    res = rv.get_json()
    assert res["success"] is True
    code = res["data"]["room_code"]

    # Join 2nd participant
    rv2 = client.post('/api/rooms/join', json={"room_code": code, "username": "Bob"})
    assert rv2.status_code == 200
    assert rv2.get_json()["success"] is True

    # Join 3rd participant -> 409 FULL
    rv3 = client.post('/api/rooms/join', json={"room_code": code, "username": "Charlie"})
    assert rv3.status_code == 409
    assert rv3.get_json()["error_code"] == "FULL"
