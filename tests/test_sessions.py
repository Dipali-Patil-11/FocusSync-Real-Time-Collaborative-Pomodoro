from app.repositories.memory_repo import MemoryRepository
from app.services.session_service import SessionService

def test_session_creation_and_joining():
    repo = MemoryRepository()
    service = SessionService(repo)

    # 1. Create session
    ok, msg, res = service.create_session("User 1")
    assert ok is True
    code = res["session_code"]
    token1 = res["participant_token"]
    assert len(code) == 6

    # 2. Join session User 2
    ok2, msg2, res2, status2 = service.join_session(code, "User 2")
    assert ok2 is True
    assert status2 == 'OK'
    assert len(res2["participants"]) == 2
    token2 = res2["participant_token"]

    # 3. Attempt join User 3 -> Must be rejected with FULL
    ok3, msg3, res3, status3 = service.join_session(code, "User 3")
    assert ok3 is False
    assert status3 == 'FULL'
    assert "full" in msg3.lower()

    # 4. Reconnect User 1
    ok_recon, msg_recon, res_recon, status_recon = service.join_session(code, "User 1", token1)
    assert ok_recon is True
    assert status_recon == 'OK'
