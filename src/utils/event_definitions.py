# event_definitions.py

from utils import min_to_sec

regular_static_events = [
    {"mode": "regular", "time": min_to_sec("00:00"), "message": "Game has started"},
    {"mode": "regular", "time": min_to_sec("01:40"), "message": "First Flagbearer spawn in 20 seconds!"},
    {"mode": "regular", "time": min_to_sec("02:30"), "message": "Glyph in 30 seconds!"},
    {"mode": "regular", "time": min_to_sec("03:00"), "message": "Glyph is now available!"},
    {"mode": "regular", "time": min_to_sec("20:00"), "message": "First Tormentor has spawned!"},
]

regular_periodic_events = [
    {"mode": "regular", "start_time": min_to_sec("05:40"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes soon!"},
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("10:00"), "message": "Flagbearer just spawned!"},
    {"mode": "regular", "start_time": min_to_sec("06:00"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("99:00"), "message": "XP Runes in 60 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("19:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Tormentor in 60 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("04:30"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Siege Creep in 30 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("99:00"), "message": "Lotus pool coming 30 seconds!"},
]

turbo_static_events = [
    {"mode": "turbo", "time": min_to_sec("00:00"), "message": "Turbo game has started"},
]

turbo_periodic_events = [
    {"mode": "turbo", "start_time": min_to_sec("02:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("99:00"), "message": "Turbo Power Runes soon!"},
    {"mode": "turbo", "start_time": min_to_sec("03:00"), "interval": min_to_sec("04:00"), "end_time": min_to_sec("99:00"), "message": "Turbo XP Runes in 60 seconds!"},
    {"mode": "turbo", "start_time": min_to_sec("10:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Turbo Tormentor in 60 seconds!"},
    {"mode": "turbo", "start_time": min_to_sec("02:15"), "interval": min_to_sec("02:30"), "end_time": min_to_sec("99:00"), "message": "Turbo Siege Creep in 30 seconds!"},
    {"mode": "turbo", "start_time": min_to_sec("01:30"), "interval": min_to_sec("01:30"), "end_time": min_to_sec("99:00"), "message": "Turbo Lotus pool coming 30 seconds!"},
]
