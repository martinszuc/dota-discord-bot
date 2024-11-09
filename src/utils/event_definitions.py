# event_definitions.py

from utils import min_to_sec

regular_static_events = [
    {"mode": "regular", "time": min_to_sec("00:00"), "message": "Game has started"},
# Creeps
    {"mode": "regular", "time": min_to_sec("01:40"), "message": "First Flagbearer in 20 seconds!"},
    {"mode": "regular", "time": min_to_sec("02:30"), "message": "Glyph in 30 seconds!"},
    {"mode": "regular", "time": min_to_sec("03:00"), "message": "Glyph is now available!"},
# Tormentor
    {"mode": "regular", "time": min_to_sec("19:00"), "message": "First Tormentor in 1 minute!"},
    {"mode": "regular", "time": min_to_sec("20:00"), "message": "First Tormentor has spawned!"},
# Neutrals
    {"mode": "regular", "time": min_to_sec("36:40"), "message": "New neutral items!"},
    {"mode": "regular", "time": min_to_sec("60:00"), "message": "New neutral items!"},
# Items
    {"mode": "turbo", "time": min_to_sec("15:00"), "message": "Shard available!"},
]

regular_periodic_events = [
# Runes
    {"mode": "regular", "start_time": min_to_sec("05:40"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes soon!"},
    {"mode": "regular", "start_time": min_to_sec("06:00"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("60:00"), "message": "XP Runes in 60 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("60:00"), "message": "Gold Runes in 30!"},
# Tormentor
    {"mode": "regular", "start_time": min_to_sec("21:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("70:00"), "message": "Don't forget Tormentor!"},
# Creeps
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("10:00"), "message": "Flagbearer just spawned!"},
    {"mode": "regular", "start_time": min_to_sec("04:30"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Siege Creep in 30 seconds!"},
# Lotus
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("16:00"), "message": "Lotus pool in 30 seconds!"},
# Neutrals
    {"mode": "regular", "start_time": min_to_sec("07:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("27:05"), "message": "New neutral items available!"},
]

turbo_static_events = [
    {"mode": "turbo", "time": min_to_sec("00:00"), "message": "Game has started"},
# Neutrals
    {"mode": "turbo", "time": min_to_sec("16:40"), "message": "New neutral items!"},
    {"mode": "turbo", "time": min_to_sec("27:16"), "message": "New neutral items!"},
# Items
    {"mode": "turbo", "time": min_to_sec("7:30"), "message": "Shard available!"},
]

turbo_periodic_events = [
# Runes
    {"mode": "turbo", "start_time": min_to_sec("02:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes soon!"},
    {"mode": "turbo", "start_time": min_to_sec("03:00"), "interval": min_to_sec("04:00"), "end_time": min_to_sec("99:00"), "message": "XP Runes in 60 seconds!"},
# Tormentor
    {"mode": "turbo", "start_time": min_to_sec("10:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Tormentor in 60 seconds!"},
# Creeps
    {"mode": "turbo", "start_time": min_to_sec("05:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("50:00"), "message": "Siege Creep in 30 seconds!"},
# Lotus
    {"mode": "turbo", "start_time": min_to_sec("01:00"), "interval": min_to_sec("01:30"), "end_time": min_to_sec("10:00"), "message": "Lotus pool coming 30 seconds!"},
]
