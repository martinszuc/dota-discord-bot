# Static events defined with 'mm:ss' time format, message, and target groups
EVENTS = {
    "05:25": ("Power rune soon!", ["mid", "supps"]),
    "06:20": ("XP rune soon!", ["off", "safe"]),
    "07:00": ("XP rune spawned!", ["off", "supps"]),
    "15:00": ("Roshan may spawn now!", ["off", "supps"]),
}

# Periodic events with start time, interval, end time, message, and target groups
PERIODIC_EVENTS = [
    ("05:40", "02:00", "40:00", ("Power runes!", ["all"])),
]
