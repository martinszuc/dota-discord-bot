from src.utils.utils import min_to_sec

# Define static events for regular game mode.
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
    {"mode": "regular", "time": min_to_sec("07:00"), "message": "Tier 1 neutral items available!"},
    {"mode": "regular", "time": min_to_sec("17:00"), "message": "Tier 2 neutral items available!"},
    {"mode": "regular", "time": min_to_sec("27:00"), "message": "Tier 3 neutral items available!"},
    {"mode": "regular", "time": min_to_sec("37:00"), "message": "Tier 4 neutral items available!"},
    {"mode": "regular", "time": min_to_sec("60:00"), "message": "Tier 5 neutral items available!"},
    # Items
    {"mode": "regular", "time": min_to_sec("10:00"), "message": "Shard available in outpost shop!"},
    {"mode": "regular", "time": min_to_sec("20:00"), "message": "Shard now available in main shop!"},
    {"mode": "regular", "time": min_to_sec("40:00"), "message": "Aghanim's Blessing available!"},
    # Outposts
    {"mode": "regular", "time": min_to_sec("07:00"), "message": "Outposts are now capturable!"},
    # Runes
    {"mode": "regular", "time": min_to_sec("02:00"), "message": "First power rune in 4 minutes!"},
    {"mode": "regular", "time": min_to_sec("14:30"), "message": "All runes will spawn at 15:00!"},
]

# Define periodic events for regular game mode.
regular_periodic_events = [
    # Power Runes (even minutes starting at 6:00)
    {"mode": "regular", "start_time": min_to_sec("05:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes in 15 seconds!"},
    # Wisdom Runes (on odd minutes starting at 7:00)
    {"mode": "regular", "start_time": min_to_sec("06:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Wisdom Runes in 15 seconds!"},
    # Water Runes (minutes 2 and 4)
    {"mode": "regular", "start_time": min_to_sec("01:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("04:00"), "message": "Water Runes in 15 seconds!"},
    # Bounty Runes (every 3 minutes starting at 0:00)
    {"mode": "regular", "start_time": min_to_sec("02:45"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("99:00"), "message": "Bounty Runes in 15 seconds!"},
    # All Runes (every 15 minutes starting at 15:00)
    {"mode": "regular", "start_time": min_to_sec("14:45"), "interval": min_to_sec("15:00"), "end_time": min_to_sec("99:00"), "message": "All Runes in 15 seconds!"},
    # Tormentor
    {"mode": "regular", "start_time": min_to_sec("21:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("70:00"), "message": "Don't forget Tormentor!"},
    # Creeps
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("01:00"), "end_time": min_to_sec("10:00"), "message": "Flagbearer just spawned!"},
    {"mode": "regular", "start_time": min_to_sec("04:30"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("99:00"), "message": "Siege Creep in 30 seconds!"},
    # Roshan location
    {"mode": "regular", "start_time": min_to_sec("20:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan bottom side!"},
    {"mode": "regular", "start_time": min_to_sec("25:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan top side!"},
    # Lotus
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("16:00"), "message": "Lotus pool in 30 seconds!"},
    {"mode": "regular", "start_time": min_to_sec("03:00"), "interval": min_to_sec("03:00"), "end_time": min_to_sec("16:00"), "message": "Lotus spawned!"},
    # Ward restocking (150 sec)
    {"mode": "regular", "start_time": min_to_sec("02:30"), "interval": min_to_sec("02:30"), "end_time": min_to_sec("99:00"), "message": "Observer Wards restocking soon!"},
]

# Define static events for turbo game mode.
turbo_static_events = [
    {"mode": "turbo", "time": min_to_sec("00:01"), "message": "Game has started"},
    # Neutrals (in turbo, neutral item timings are 40% of regular timings)
    {"mode": "turbo", "time": min_to_sec("03:00"), "message": "Tier 1 neutral items available!"},
    {"mode": "turbo", "time": min_to_sec("07:00"), "message": "Tier 2 neutral items available!"},
    {"mode": "turbo", "time": min_to_sec("11:00"), "message": "Tier 3 neutral items available!"},
    {"mode": "turbo", "time": min_to_sec("15:00"), "message": "Tier 4 neutral items available!"},
    {"mode": "turbo", "time": min_to_sec("24:00"), "message": "Tier 5 neutral items available!"},
    # Items
    {"mode": "turbo", "time": min_to_sec("05:00"), "message": "Shard available!"},
    {"mode": "turbo", "time": min_to_sec("20:00"), "message": "Aghanim's Blessing available!"},
    # Tormentor
    {"mode": "turbo", "time": min_to_sec("09:00"), "message": "Tormentor in 60 seconds!"},
    {"mode": "turbo", "time": min_to_sec("10:00"), "message": "Tormentor spawned!"},
    # Outposts
    {"mode": "turbo", "time": min_to_sec("03:00"), "message": "Outposts are now capturable!"},
    # Runes
    {"mode": "turbo", "time": min_to_sec("00:30"), "message": "First power rune in 2 minutes!"},
    {"mode": "turbo", "time": min_to_sec("06:30"), "message": "All runes will spawn at 07:00!"},
]

# Define periodic events for turbo game mode.
turbo_periodic_events = [
    # Power Runes (in turbo, spawns at 2:00 and then every 2 minutes)
    {"mode": "turbo", "start_time": min_to_sec("01:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Power Runes in 15 seconds!"},
    # Wisdom Runes (in turbo, spawns at 3:00 and then every 2 minutes)
    {"mode": "turbo", "start_time": min_to_sec("02:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Wisdom Runes in 15 seconds!"},
    # Bounty Runes (in turbo, spawns at 0:00 and then every 2 minutes)
    {"mode": "turbo", "start_time": min_to_sec("01:45"), "interval": min_to_sec("02:00"), "end_time": min_to_sec("99:00"), "message": "Bounty Runes in 15 seconds!"},
    # All Runes (in turbo, spawns every 7 minutes starting at 7:00)
    {"mode": "turbo", "start_time": min_to_sec("06:45"), "interval": min_to_sec("07:00"), "end_time": min_to_sec("99:00"), "message": "All Runes in 15 seconds!"},
    # Creeps
    {"mode": "turbo", "start_time": min_to_sec("05:00"), "interval": min_to_sec("05:00"), "end_time": min_to_sec("50:00"), "message": "Siege Creep in 30 seconds!"},
    # Lotus
    {"mode": "turbo", "start_time": min_to_sec("01:00"), "interval": min_to_sec("01:30"), "end_time": min_to_sec("13:00"), "message": "Lotus pool in 30 seconds!"},
    # Roshan
    {"mode": "turbo", "start_time": min_to_sec("10:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan bottom side!"},
    {"mode": "turbo", "start_time": min_to_sec("15:00"), "interval": min_to_sec("10:00"), "end_time": min_to_sec("99:00"), "message": "Roshan top side!"},
    # Ward restocking (in turbo, 75 seconds)
    {"mode": "turbo", "start_time": min_to_sec("01:15"), "interval": min_to_sec("01:15"), "end_time": min_to_sec("99:00"), "message": "Observer Wards restocking soon!"},
]

# Define mindful messages to be periodically sent to encourage positive play.
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
    {"message": "Remember, it's just a game. Have fun and relax!"},
    {"message": "Communication is key - use your voice and pings wisely!"},
    {"message": "Don't forget to check the minimap regularly!"},
    {"message": "Take a moment to check your item builds and adapting if needed!"},
    {"message": "Smoke of Deceit can turn the game around!"},
    {"message": "Remember to check enemy inventories for key items!"},
]

# Define pre-mindful messages to introduce audio calming sounds.
mindful_pre_messages = [
    {"message": "Take a deep breath. Here are a few moments of soothing nature sounds, just for you."},
    {"message": "For a brief pause, listen to these calming sounds from nature. Let yourself unwind."},
    {"message": "Close your eyes if you can, and let these sounds of nature bring you a moment of peace."},
    {"message": "Here's a moment of tranquility to help you feel calm and centered. Enjoy the sounds of nature."},
    {"message": "A little relaxation break for you. Let these calming sounds wash over you and release any tension."},
    {"message": "For a few moments, immerse yourself in these peaceful nature sounds. A small escape to relax."},
    {"message": "Here's 30 seconds of serene nature sounds to help bring you calm and ease your mind."},
    {"message": "Take a moment to relax. Here's a brief escape into nature to help you recharge."},
    {"message": "Allow yourself to slow down. Here's a snippet of nature's calm to help you refocus and relax."},
    {"message": "This is your reminder to breathe and let go. Listen to these sounds of nature to find calm."},
]