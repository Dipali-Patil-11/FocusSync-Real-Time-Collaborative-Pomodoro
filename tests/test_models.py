from app.models.room import Room, generate_room_code
from app.models.participant import Participant
from app.models.timer import TimerState
from app.models.settings import RoomSettings

def test_room_model():
    code = generate_room_code()
    assert len(code) == 6
    assert code.isupper()

    room = Room(room_code=code, creator_token="token-123")
    assert room.room_code == code
    assert room.status == "ACTIVE"
    assert room.to_dict()["room_code"] == code

def test_participant_model():
    p = Participant(participant_token="token-1", room_code="ABCDEF", username="Alice", slot=1)
    assert p.username == "Alice"
    assert p.slot == 1
    assert p.is_online is True

def test_timer_model():
    t = TimerState(room_code="ABCDEF", mode="FOCUS", duration=1500, remaining_seconds=1500)
    assert t.remaining_seconds == 1500
    assert t.calculate_current_remaining() == 1500

def test_settings_model():
    s = RoomSettings(room_code="ABCDEF")
    assert s.focus_duration == 25
    assert s.short_break_duration == 5
    assert s.long_break_duration == 15
