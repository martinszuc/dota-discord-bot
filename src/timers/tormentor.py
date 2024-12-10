# src/timers/tormentor.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.utils.config import logger

class TormentorTimer(BaseTimer):
    """Manages the Tormentor respawn timer via a separate command."""

    def setup(self):
        """Set up the Tormentor respawn timer based on mode."""
        self.respawn_duration = 10 * 60 if self.game_timer.mode == 'regular' else 5 * 60  # 10 minutes or 5 minutes
        self.is_running = False
        self.next_announcements = []

        logger.info(f"TormentorTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self):
        """Start the Tormentor respawn timer."""
        if self.is_running:
            logger.warning(f"TormentorTimer is already running for guild ID {self.game_timer.guild_id}.")
            return

        current_time = self.game_timer.time_elapsed
        self.is_running = True
        self.next_announcements = [
            (current_time + 1, "Tormentor killed! Starting respawn timer."),
            (current_time + self.respawn_duration - 180, "Tormentor will respawn in 3 minutes!"),
            (current_time + self.respawn_duration - 60, "Tormentor will respawn in 1 minute!"),
            (current_time + self.respawn_duration, "Tormentor has respawned!")
        ]
        logger.info(f"TormentorTimer started for guild ID {self.game_timer.guild_id} with respawn duration of {self.respawn_duration} seconds.")

    async def check_and_announce(self):
        """Check the Tormentor timer and announce events if necessary."""
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"TormentorTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        if not self.next_announcements:
            await self.stop()

    async def stop(self):
        """Stop the Tormentor timer."""
        self.is_running = False
        self.next_announcements = []
        logger.info(f"TormentorTimer stopped for guild ID {self.game_timer.guild_id}.")
