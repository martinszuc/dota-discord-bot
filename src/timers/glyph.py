# src/timers/glyph.py

from src.timers.base import BaseTimer
from src.utils.utils import min_to_sec
from src.event_definitions import regular_static_events, turbo_static_events
from src.utils.config import logger

class GlyphTimer(BaseTimer):
    """Manages the Glyph cooldown timer."""

    def setup(self):
        """Set up the Glyph timer based on the game mode."""
        if self.game_timer.mode == 'regular':
            cooldown_duration = 5 * 60  # 5 minutes for regular
        else:
            cooldown_duration = 3 * 60  # 3 minutes for turbo

        # Schedule announcements
        current_time = self.game_timer.time_elapsed
        self.next_announcements = [
            (current_time + cooldown_duration - 60, "Enemy glyph available in 1 minute!"),
            (current_time + cooldown_duration, "Enemy glyph is now available!")
        ]
        self.is_running = True
        logger.info(f"GlyphTimer set up for guild ID {self.game_timer.guild_id} with cooldown {cooldown_duration} seconds.")

    async def check_and_announce(self):
        if not self.is_running or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        due = [a for a in self.next_announcements if a[0] == current_time]
        for _, msg in due:
            await self.announcement.announce(self.game_timer, msg)
            logger.info(f"GlyphTimer announcement: '{msg}'")
            self.next_announcements.remove((_, msg))

        # If all announcements are done, reset the timer
        if not self.next_announcements:
            self.reset()
