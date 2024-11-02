# events.py

# Static events defined with unique IDs, 'MM:SS' time format, message, and target groups
STATIC_EVENTS = {
    1: {"time": "05:25", "message": "🛡️ **Power Rune soon!**", "target_groups": ["mid", "supps"]},
    2: {"time": "06:20", "message": "💎 **XP Rune soon!**", "target_groups": ["off", "safe"]},
    3: {"time": "07:00", "message": "💎 **XP Rune spawned!**", "target_groups": ["off", "supps"]},
}

# Periodic events defined with unique IDs, start time, interval, end time, message, and target groups
PERIODIC_EVENTS = {
    1: {"start_time": "05:40", "interval": "02:00", "end_time": "40:00", "message": "🔄 **Power Runes!**", "target_groups": ["all"]},
}
