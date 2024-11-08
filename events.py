# events.py

from utils import parse_time

class EventsManager:
    """Class to manage events for different game modes."""

    def __init__(self):
        self.events = {
            'regular': {
                'static': {
                    1: {"time": "00:01", "message": "Game has started"},
                    2: {"time": "01:30", "message": "First Flagbearer in 30 seconds!"},
                    3: {"time": "02:00", "message": "First Flagbearer spawned!"},
                    4: {"time": "20:00", "message": "First Tormentor has spawned!"},
                    5: {"time": "02:30", "message": "Glyph in 30 seconds!"},
                    6: {"time": "03:00", "message": "Glyph is now available!"},
                },
                'periodic': {
                    1: {"start_time": "05:40", "interval": "02:00", "end_time": "99:00", "message": "Power Runes soon!"},
                    2: {"start_time": "06:00", "interval": "07:00", "end_time": "99:00", "message": "XP Runes in 60 seconds!"},
                    3: {"start_time": "19:00", "interval": "10:00", "end_time": "99:00", "message": "Tormentor in 60 seconds!"},
                    4: {"start_time": "04:30", "interval": "05:00", "end_time": "99:00", "message": "Siege Creep in 30 seconds!"},
                    5: {"start_time": "03:00", "interval": "03:00", "end_time": "99:00", "message": "Lotus pool coming 30 seconds!"},
                }
            },
            'turbo': {
                'static': {
                    1: {"time": "00:01", "message": "Turbo game has started"},
                    # Add more turbo-specific static events if needed
                },
                'periodic': {
                    1: {"start_time": "02:00", "interval": "01:00", "end_time": "99:00", "message": "Turbo Power Runes soon!"},
                    2: {"start_time": "03:00", "interval": "04:00", "end_time": "99:00", "message": "Turbo XP Runes in 60 seconds!"},
                    3: {"start_time": "10:00", "interval": "05:00", "end_time": "99:00", "message": "Turbo Tormentor in 60 seconds!"},
                    4: {"start_time": "02:15", "interval": "02:30", "end_time": "99:00", "message": "Turbo Siege Creep in 30 seconds!"},
                    5: {"start_time": "01:30", "interval": "01:30", "end_time": "99:00", "message": "Turbo Lotus pool coming 30 seconds!"},
                }
            }
        }

    def get_static_events(self, mode='regular'):
        """Retrieve static events for the specified game mode."""
        return self.events.get(mode, {}).get('static', {})

    def get_periodic_events(self, mode='regular'):
        """Retrieve periodic events for the specified game mode."""
        return self.events.get(mode, {}).get('periodic', {})

