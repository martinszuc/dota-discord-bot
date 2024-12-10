# src/timers/roshan.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.utils.config import logger

class RoshanTimer(BaseTimer):
    """Manages Roshan spawn logic via a separate command."""

    def setup(self):
        """Set up the Roshan respawn schedule based on the mode."""
        mode = self.game_timer.mode

        if mode == 'turbo':
            self.min_respawn = 4 * 60  # Turbo mode: 4 minutes minimum respawn
            self.max_respawn = 5.5 * 60  # Turbo mode: 5.5 minutes max respawn
        else:
            self.min_respawn = 8 * 60  # Regular mode: 8 minutes minimum respawn
            self.max_respawn = 11 * 60  # Regular mode: 11 minutes max respawn

        self.is_running = False
        self.next_announcements = []

        logger.info(f"RoshanTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self):
        """Start the Roshan timer."""
        if self.is_running:
            logger.warning(f"RoshanTimer is already running for guild ID {self.game_timer.guild_id}.")
            return

        current_time = self.game_timer.time_elapsed
        self.is_running = True
        self.next_announcements = [
            (current_time + 1, "Roshan killed! Starting respawn timer."),
            (current_time + self.min_respawn - 300, "Roshan may respawn in 5 minutes!"),
            (current_time + self.min_respawn - 180, "Roshan may respawn in 3 minutes!"),
            (current_time + self.min_respawn - 60, "Roshan may respawn in 1 minute!"),
            (current_time + self.min_respawn, "Roshan may be up now!"),
            (current_time + self.max_respawn, "Roshan is definitely up!")
        ]
        logger.info(f"RoshanTimer started for guild ID {self.game_timer.guild_id} with respawn window between {self.min_respawn} and {self.max_respawn} seconds.")

    async def check_and_announce(self):
        """Check the Roshan timer and announce events if necessary."""
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"RoshanTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        if not self.next_announcements:
            await self.stop()

    async def stop(self):
        """Stop the Roshan timer."""
        self.is_running = False
        self.next_announcements = []
        logger.info(f"RoshanTimer stopped for guild ID {self.game_timer.guild_id}.")
