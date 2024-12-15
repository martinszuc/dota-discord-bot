# src/timers/glyph.py

import asyncio
from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger

class GlyphTimer(BaseTimer):
    """Class to handle the Glyph cooldown timer."""

    def __init__(self, game_timer):
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"GlyphTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel):
        try:
            logger.info(f"GlyphTimer running for guild ID {self.game_timer.guild_id}.")

            if self.game_timer.mode == 'regular':
                cooldown_duration = 5 * 60  # 5 minutes
            else:
                cooldown_duration = 3 * 60  # 3 minutes

            await self.announcement.announce(self.game_timer, "Enemy glyph activated. Cooldown started.")
            logger.info(f"Glyph cooldown started for guild ID {self.game_timer.guild_id}.")

            # Warnings for glyph availability
            warnings = [
                (cooldown_duration - 60, "Enemy glyph available in 1 minute!"),
                (60,                     "Enemy glyph is now available!")
            ]
            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"GlyphTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"GlyphTimer concluded for guild ID {self.game_timer.guild_id}.")
