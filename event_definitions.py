# event_definitions.py

def time_to_seconds(time_str):
    """Convert 'MM:SS' format to seconds."""
    minutes, seconds = map(int, time_str.split(":"))
    return minutes * 60 + seconds

regular_static_events = {
    # ID is removed to let the database handle it
    "game_start": {"time": time_to_seconds("00:01"), "message": "Game has started"},
    "first_flagbearer_warning": {"time": time_to_seconds("01:30"), "message": "First Flagbearer in 30 seconds!"},
    "first_flagbearer_spawn": {"time": time_to_seconds("02:00"), "message": "First Flagbearer spawned!"},
    "first_tormentor_spawn": {"time": time_to_seconds("20:00"), "message": "First Tormentor has spawned!"},
    "glyph_warning": {"time": time_to_seconds("02:30"), "message": "Glyph in 30 seconds!"},
    "glyph_available": {"time": time_to_seconds("03:00"), "message": "Glyph is now available!"},
}

regular_periodic_events = {
    "power_runes": {"start_time": time_to_seconds("05:40"), "interval": time_to_seconds("02:00"), "end_time": time_to_seconds("99:00"), "message": "Power Runes soon!"},
    "xp_runes": {"start_time": time_to_seconds("06:00"), "interval": time_to_seconds("07:00"), "end_time": time_to_seconds("99:00"), "message": "XP Runes in 60 seconds!"},
    "tormentor": {"start_time": time_to_seconds("19:00"), "interval": time_to_seconds("10:00"), "end_time": time_to_seconds("99:00"), "message": "Tormentor in 60 seconds!"},
    "siege_creep": {"start_time": time_to_seconds("04:30"), "interval": time_to_seconds("05:00"), "end_time": time_to_seconds("99:00"), "message": "Siege Creep in 30 seconds!"},
    "lotus_pool": {"start_time": time_to_seconds("03:00"), "interval": time_to_seconds("03:00"), "end_time": time_to_seconds("99:00"), "message": "Lotus pool coming 30 seconds!"},
}

turbo_static_events = {
    "turbo_game_start": {"time": time_to_seconds("00:01"), "message": "Turbo game has started"},
}

turbo_periodic_events = {
    "turbo_power_runes": {"start_time": time_to_seconds("02:00"), "interval": time_to_seconds("01:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo Power Runes soon!"},
    "turbo_xp_runes": {"start_time": time_to_seconds("03:00"), "interval": time_to_seconds("04:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo XP Runes in 60 seconds!"},
    "turbo_tormentor": {"start_time": time_to_seconds("10:00"), "interval": time_to_seconds("05:00"), "end_time": time_to_seconds("99:00"), "message": "Turbo Tormentor in 60 seconds!"},
    "turbo_siege_creep": {"start_time": time_to_seconds("02:15"), "interval": time_to_seconds("02:30"), "end_time": time_to_seconds("99:00"), "message": "Turbo Siege Creep in 30 seconds!"},
    "turbo_lotus_pool": {"start_time": time_to_seconds("01:30"), "interval": time_to_seconds("01:30"), "end_time": time_to_seconds("99:00"), "message": "Turbo Lotus pool coming 30 seconds!"},
}
