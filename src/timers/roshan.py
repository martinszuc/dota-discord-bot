# src/timers/roshan.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.utils.config import logger

class RoshanTimer(BaseTimer):
    """Manages Roshan spawn logic via the main game timer."""

    def setup(self):
        """Set up the Roshan respawn schedule based on current mode and time_elapsed."""
        self.is_running = True
        mode = self.game_timer.mode
        current_time = self.game_timer.time_elapsed

        if mode == 'turbo':
            min_respawn = 4 * 60  # Turbo mode: 4 minutes minimum respawn
            max_respawn = 5.5 * 60  # Turbo mode: 5.5 minutes max respawn
        else:
            min_respawn = 8 * 60  # Regular mode: 8 minutes minimum respawn
            max_respawn = 11 * 60  # Regular mode: 11 minutes max respawn

        # Schedule announcements relative to current_time
        self.next_announcements = [
            (current_time + 1, "Roshan killed! Starting respawn timer."),
            (current_time + min_respawn - 300, "Roshan may respawn in 5 minutes!"),
            (current_time + min_respawn - 180, "Roshan may respawn in 3 minutes!"),
            (current_time + min_respawn - 60, "Roshan may respawn in 1 minute!"),
            (current_time + min_respawn, "Roshan may be up now!"),
            (current_time + max_respawn, "Roshan is definitely up!")
        ]
        logger.info(f"RoshanTimer set up for guild ID {self.game_timer.guild_id} with respawn between {min_respawn} and {max_respawn} seconds.")

    async def check_and_announce(self):
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"RoshanTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        # If all announcements are done, reset the timer
        if not self.next_announcements:
            self.reset()
