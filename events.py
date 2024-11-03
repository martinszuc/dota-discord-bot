# events.py

# Static events defined with unique IDs, 'MM:SS' time format, and message
STATIC_EVENTS = {
    1: {"time": "00:01", "message": "Game has started"},
    2: {"time": "01:30", "message": "First Flagbearer creep spawning in 30 seconds!"},
    3: {"time": "02:00", "message": "First Flagbearer creep has spawned!"},
    4: {"time": "20:00", "message": "First Tormentor has spawned!"},
    5: {"time": "02:00", "message": "Glyph will be available in 30 seconds!"},
    6: {"time": "02:30", "message": "Glyph is now available!"},
    7: {"time": "00:20", "message": "Thomas stinks"},
    8: {"time": "00:10", "message": "Dano je kokot!"},
}

# Periodic events defined with unique IDs, start time, interval, end time, and message
PERIODIC_EVENTS = {
    1: {"start_time": "05:40", "interval": "02:00", "end_time": "99:00", "message": "Power Runes spawning soon!"},
    2: {"start_time": "06:00", "interval": "07:00", "end_time": "99:00", "message": "XP Runes spawning in 60 seconds!"},
    3: {"start_time": "19:00", "interval": "10:00", "end_time": "99:00", "message": "Tormentor spawning in 60 seconds!"},
    4: {"start_time": "04:30", "interval": "05:00", "end_time": "99:00", "message": "Siege Creep spawning in 30 seconds!"},
    5: {"start_time": "07:00", "interval": "07:00", "end_time": "99:00", "message": "Smoke will restock in 1 minute!"},
}
