# events.py

# Static events defined with unique IDs, 'MM:SS' time format, message, and target groups
STATIC_EVENTS = {
    1: {"time": "00:00", "message": "🛡️ **Game has started**", "target_groups": ["all"]},
    2: {"time": "03:30", "message": "🛡️ **Power Rune spawning in 30 seconds!**", "target_groups": ["mid", "supps"]},
    3: {"time": "01:30", "message": "🚩 **First Flagbearer creep spawning in 30 seconds!**", "target_groups": ["all"]},
    4: {"time": "02:00", "message": "🚩 **First Flagbearer creep has spawned!**", "target_groups": ["all"]},
    5: {"time": "20:00", "message": "💥 **First Tormentor has spawned!**", "target_groups": ["all"]},
    6: {"time": "02:00", "message": "🛡️ **Glyph will be available in 30 seconds!**", "target_groups": ["all"]},
    7: {"time": "02:30", "message": "🛡️ **Glyph is now available!**", "target_groups": ["all"]},
}

# Periodic events defined with unique IDs, start time, interval, end time, message, and target groups
PERIODIC_EVENTS = {
    1: {"start_time": "05:40", "interval": "02:00", "end_time": "99:00", "message": "🔄 **Power Runes spawning soon!**", "target_groups": ["all"]},
    2: {"start_time": "06:00", "interval": "07:00", "end_time": "99:00", "message": "💎 **XP Runes spawning in 60 seconds!**", "target_groups": ["all"]},
    3: {"start_time": "19:00", "interval": "10:00", "end_time": "99:00", "message": "💥 **Tormentor spawning in 60 seconds!**", "target_groups": ["all"]},
    4: {"start_time": "04:30", "interval": "05:00", "end_time": "99:00", "message": "🚚 **Siege Creep spawning in 30 seconds!**", "target_groups": ["all"]},
    5: {"start_time": "07:00", "interval": "07:00", "end_time": "99:00", "message": "💨 **Smoke will restock in 1 minute!**", "target_groups": ["all"]},
}