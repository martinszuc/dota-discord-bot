# src/timers/glyph.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.event_definitions import regular_static_events, turbo_static_events
from src.utils.config import logger

class GlyphTimer(BaseTimer):
    """Manages the Glyph cooldown timer via a separate command."""

    def setup(self):
        """Set up the Glyph cooldown based on mode."""
        self.cooldown_duration = 5 * 60 if self.game_timer.mode == 'regular' else 3 * 60  # 5 minutes or 3 minutes
        self.is_running = False
        self.next_announcements = []

        logger.info(f"GlyphTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self):
        """Start the Glyph cooldown timer."""
        if self.is_running:
            logger.warning(f"GlyphTimer is already running for guild ID {self.game_timer.guild_id}.")
            return

        current_time = self.game_timer.time_elapsed
        self.is_running = True
        self.next_announcements = [
            (current_time + 1, "Enemy glyph activated. Cooldown started."),
            (current_time + self.cooldown_duration - 60, "Enemy glyph available in 1 minute!"),
            (current_time + self.cooldown_duration, "Enemy glyph is now available!")
        ]
        logger.info(f"GlyphTimer started for guild ID {self.game_timer.guild_id} with cooldown of {self.cooldown_duration} seconds.")

    async def check_and_announce(self):
        """Check the Glyph timer and announce events if necessary."""
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"GlyphTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        if not self.next_announcements:
            await self.stop()

    async def stop(self):
        """Stop the Glyph timer."""
        self.is_running = False
        self.next_announcements = []
        logger.info(f"GlyphTimer stopped for guild ID {self.game_timer.guild_id}.")
