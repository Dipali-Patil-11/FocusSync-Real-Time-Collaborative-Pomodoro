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

    # 2. Join session Users 2, 3, 4, 5
    for i in range(2, 6):
        ok_i, msg_i, res_i, status_i = service.join_session(code, f"User {i}")
        assert ok_i is True
        assert status_i == 'OK'
        assert len(res_i["participants"]) == i

    # 3. Attempt join User 6 -> Must be rejected with FULL
    ok6, msg6, res6, status6 = service.join_session(code, "User 6")
    assert ok6 is False
    assert status6 == 'FULL'
    assert "full" in msg6.lower()

    # 4. Reconnect User 1
    ok_recon, msg_recon, res_recon, status_recon = service.join_session(code, "User 1", token1)
    assert ok_recon is True
    assert status_recon == 'OK'

    # 5. Slot Recycling: User 3 leaves -> User 6 joins -> receives slot 3
    participants = repo.get_participants_by_session(code)
    p3 = [p for p in participants if p.username == "User 3"][0]
    service.leave_session(p3.participant_token)

    ok_recycled, msg_recycled, res_recycled, status_recycled = service.join_session(code, "User 6 Recycled")
    assert ok_recycled is True
    assert status_recycled == 'OK'
    new_p6 = res_recycled["participant"]
    assert new_p6["slot"] == 3
