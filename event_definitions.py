# event_definitions.py

def time_to_seconds(time_str):
    """Convert 'MM:SS' format to seconds."""
    minutes, seconds = map(int, time_str.split(":"))
    return minutes * 60 + seconds

regular_static_events = [
    {"mode": "regular", "time": time_to_seconds("00:01"), "message": "Game has started"},
    {"mode": "regular", "time": time_to_seconds("01:30"), "message": "First Flagbearer in 30 seconds!"},
    {"mode": "regular", "time": time_to_seconds("02:00"), "message": "First Flagbearer spawned!"},
    {"mode": "regular", "time": time_to_seconds("20:00"), "message": "First Tormentor has spawned!"},
    {"mode": "regular", "time": time_to_seconds("02:30"), "message": "Glyph in 30 seconds!"},
    {"mode": "regular", "time": time_to_seconds("03:00"), "message": "Glyph is now available!"},
]

regular_periodic_events = [
    {"mode": "regular", "start_time": time_to_seconds("05:40"), "interval": time_to_seconds("02:00"), "end_time": time_to_seconds("99:00"), "message": "Power Runes soon!"},
    {"mode": "regular", "start_time": time_to_seconds("06:00"), "interval": time_to_seconds("07:00"), "end_time": time_to_seconds("99:00"), "message": "XP Runes in 60 seconds!"},
    {"mode": "regular", "start_time": time_to_seconds("19:00"), "interval": time_to_seconds("10:00"), "end_time": time_to_seconds("99:00"), "message": "Tormentor in 60 seconds!"},
    {"mode": "regular", "start_time": time_to_seconds("04:30"), "interval": time_to_seconds("05:00"), "end_time": time_to_seconds("99:00"), "message": "Siege Creep in 30 seconds!"},
    {"mode": "regular", "start_time": time_to_seconds("03:00"), "interval": time_to_seconds("03:00"), "end_time": time_to_seconds("99:00"), "message": "Lotus pool coming 30 seconds!"},
]

turbo_static_events = [
    {"mode": "turbo", "time": time_to_seconds("00:01"), "message": "Turbo game has started"},
]

turbo_periodic_events = [
    {"mode": "turbo", "start_time": time_to_seconds("02:00"), "interval": time_to_seconds("01:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo Power Runes soon!"},
    {"mode": "turbo", "start_time": time_to_seconds("03:00"), "interval": time_to_seconds("04:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo XP Runes in 60 seconds!"},
    {"mode": "turbo", "start_time": time_to_seconds("10:00"), "interval": time_to_seconds("05:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo Tormentor in 60 seconds!"},
    {"mode": "turbo", "start_time": time_to_seconds("02:15"), "interval": time_to_seconds("02:30"), "end_time": time_to_seconds("99:00"), "message": "Turbo Siege Creep in 30 seconds!"},
    {"mode": "turbo", "start_time": time_to_seconds("01:30"), "interval": time_to_seconds("01:30"), "end_time": time_to_seconds("99:00"), "message": "Turbo Lotus pool coming 30 seconds!"},
]
