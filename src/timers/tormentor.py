# src/timers/tormentor.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.utils.config import logger

class TormentorTimer(BaseTimer):
    """Handles the Tormentor respawn timer."""

    def setup(self):
        """Set up the Tormentor respawn schedule based on game mode."""
        self.is_running = True
        mode = self.game_timer.mode
        current_time = self.game_timer.time_elapsed

        if mode == 'regular':
            respawn_duration = 10 * 60  # 10 minutes for regular
        else:
            respawn_duration = 5 * 60  # 5 minutes for turbo

        # Schedule announcements relative to current_time
        self.next_announcements = [
            (current_time + respawn_duration - 180, "Tormentor will respawn in 3 minutes!"),
            (current_time + respawn_duration - 60, "Tormentor will respawn in 1 minute!"),
            (current_time + respawn_duration, "Tormentor has respawned!")
        ]
        logger.info(f"TormentorTimer set up for guild ID {self.game_timer.guild_id} with respawn in {respawn_duration} seconds.")

    async def check_and_announce(self):
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"TormentorTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        # If all announcements are done, reset the timer
        if not self.next_announcements:
            self.reset()
