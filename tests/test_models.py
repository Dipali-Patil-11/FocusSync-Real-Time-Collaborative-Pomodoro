from app.models.session import Session, generate_session_code
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import SessionSettings

def test_session_model():
    code = generate_session_code()
    assert len(code) == 6
    assert code.isupper()

    session = Session(session_code=code, creator_token="token-123")
    assert session.session_code == code
    assert session.status == "ACTIVE"
    assert session.to_dict()["session_code"] == code

def test_participant_model():
    p = Participant(participant_token="token-1", session_code="ABCDEF", username="Alice", slot=1)
    assert p.username == "Alice"
    assert p.slot == 1
    assert p.is_online is True

def test_timer_model():
    t = TimerState(session_code="ABCDEF", mode="FOCUS", duration=1500, remaining_seconds=1500)
    assert t.remaining_seconds == 1500
    assert t.calculate_current_remaining() == 1500

def test_settings_model():
    s = SessionSettings(session_code="ABCDEF")
    assert s.focus_duration == 25
    assert s.short_break_duration == 5
    assert s.long_break_duration == 15
