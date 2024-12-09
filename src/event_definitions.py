# event_definitions.py

from src.utils.utils import min_to_sec
regular_static_events = [
    {"mode": "regular", "time": min_to_sec("00:01"), "message": "Game has started"},
# Creeps
    {"mode": "regular", "time": min_to_sec("01:40"), "message": "First Flagbearer in 20 seconds!"},
    {"mode": "regular", "time": min_to_sec("02:30"), "message": "Glyph in 30 seconds!"},
    {"mode": "regular", "time": min_to_sec("03:00"), "message": "Glyph is now available!"},
# Tormentor
    {"mode": "regular", "time": min_to_sec("19:00"), "message": "First Tormentor in 1 minute!"},
    {"mode": "regular", "time": min_to_sec("20:00"), "message": "Tormentor has spawned!"},
# Neutrals
    {"mode": "regular", "time": min_to_sec("36:40"), "message": "New neutral items!"},
    {"mode": "regular", "time": min_to_sec("59:30"), "message": "New neutral items in 30 seconds!"},
    {"mode": "regular", "time": min_to_sec("60:00"), "message": "New neutral items!"},
# Items
    {"mode": "regular", "time": min_to_sec("15:00"), "message": "Shard available!"},
]


regular_periodic_events = [
# Runes
    {"mode": "regular", "start_time": min_to_sec("05:40"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes soon!"},
    {"mode": "regular", "start_time": min_to_sec("06:00"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("60:00"), "message": "XP Runes in 60 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("60:00"), "message": "Gold Runes in 30 seconds!"},
# Tormentor
    {"mode": "regular", "start_time": min_to_sec("21:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("70:00"), "message": "Don't forget Tormentor!"},
# Creeps
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("10:00"), "message": "Flagbearer just spawned!"},
    {"mode": "regular", "start_time": min_to_sec("04:30"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Siege Creep in 30 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("20:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan bottom side!"},
    {"mode": "regular", "start_time": min_to_sec("25:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan top side!"},
# Lotus
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("16:00"), "message": "Lotus pool in 30 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("16:00"), "message": "Lotus spawned!"},
# Neutrals
    {"mode": "regular", "start_time": min_to_sec("07:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("27:05"), "message": "New neutral items available!"},
# Items
    {"mode": "regular", "start_time": min_to_sec("02:15"), "interval": min_to_sec("02:15"), "end_time": min_to_sec("07:30"), "message": "Wards now available!"},
]

turbo_static_events = [
    {"mode": "turbo", "time": min_to_sec("00:01"), "message": "Game has started"},
# Neutrals
    {"mode": "turbo", "time": min_to_sec("16:40"), "message": "New neutral items!"},
    {"mode": "turbo", "time": min_to_sec("27:16"), "message": "New neutral items!"},
# Items
    {"mode": "turbo", "time": min_to_sec("7:30"), "message": "Shard available!"},
]

turbo_periodic_events = [
# Runes
    {"mode": "turbo", "start_time": min_to_sec("05:30"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes in 30 seconds!!"},
    {"mode": "turbo", "start_time": min_to_sec("01:40"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("4:10"), "message": "Water runes in 20 seconds!!"},
    {"mode": "turbo", "start_time": min_to_sec("06:00"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("99:00"), "message": "XP Runes in 60 seconds!"},
    {"mode": "turbo", "start_time": min_to_sec("06:30"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("99:00"), "message": "XP Runes in 30 seconds!"},
# Tormentor
    {"mode": "turbo", "start_time": min_to_sec("10:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Tormentor in 60 seconds!"},
# Creeps
    {"mode": "turbo", "start_time": min_to_sec("05:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("50:00"), "message": "Siege Creep in 30 seconds!"},
# Lotus
    {"mode": "turbo", "start_time": min_to_sec("01:00"), "interval": min_to_sec("01:30"), "end_time": min_to_sec("13:00"), "message": "Lotus pool in 30 seconds!"},
# Roshan

    {"mode": "turbo", "start_time": min_to_sec("10:00"), "interval": min_to_sec("10:00"),
     "end_time": min_to_sec("99:00"), "message": "Roshan bottom side!"},
    {"mode": "turbo", "start_time": min_to_sec("15:00"), "interval": min_to_sec("10:00"),
     "end_time": min_to_sec("99:00"), "message": "Roshan top side!"},
]

mindful_messages = [
    {"message": "Remember to take a deep breath and stay calm!"},
    {"message": "Focus on your strategy and enjoy the game!"},
    {"message": "You're doing great — keep it up!"},
    {"message": "You are loved!"},
    {"message": "Win or lose, every game is a learning experience!"},
    {"message": "Take it easy, stay positive, and give your best!"},
    {"message": "Remember, teamwork is the key to victory!"},
    {"message": "Stay focused and have fun!"},
    {"message": "Enjoy the game and play at your own pace!"},
    {"message": "Stay hydrated, and keep your cool!"},
    {"message": "Remember, it’s just a game. Have fun and relax!"},
]
mindful_pre_messages = [
    {"message": "Take a deep breath. Here are a few moments of soothing nature sounds, just for you."},
    {"message": "For a brief pause, listen to these calming sounds from nature. Let yourself unwind."},
    {"message": "Close your eyes if you can, and let these sounds of nature bring you a moment of peace."},
    {"message": "Here’s a moment of tranquility to help you feel calm and centered. Enjoy the sounds of nature."},
    {"message": "A little relaxation break for you. Let these calming sounds wash over you and release any tension."},
    {"message": "For a few moments, immerse yourself in these peaceful nature sounds. A small escape to relax."},
    {"message": "Here’s 30 seconds of serene nature sounds to help bring you calm and ease your mind."},
    {"message": "Take a moment to relax. Here’s a brief escape into nature to help you recharge."},
    {"message": "Allow yourself to slow down. Here’s a snippet of nature’s calm to help you refocus and relax."},
    {"message": "This is your reminder to breathe and let go. Listen to these sounds of nature to find calm."},
]

