from dataclasses import dataclass

@dataclass
class RoomSettings:
    room_code: str
    focus_duration: int = 25     # in minutes
    short_break_duration: int = 5 # in minutes
    long_break_duration: int = 15 # in minutes
    auto_start: bool = False
    sound_enabled: bool = True

    def to_dict(self):
        return {
            "room_code": self.room_code,
            "focus_duration": self.focus_duration,
            "short_break_duration": self.short_break_duration,
            "long_break_duration": self.long_break_duration,
            "auto_start": self.auto_start,
            "sound_enabled": self.sound_enabled
        }
