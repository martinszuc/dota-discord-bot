# src/timers/glyph.py

import asyncio
from communication.announcement import Announcement
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
            # Set cooldown duration based on game mode
            if self.game_timer.mode == 'regular':
                cooldown_duration = 5 * 60  # 5 minutes for regular
                logger.debug(f"Regular mode: Glyph cooldown in {cooldown_duration} seconds.")
            else:
                cooldown_duration = 3 * 60  # 3 minutes for turbo
                logger.debug(f"Turbo mode: Glyph cooldown in {cooldown_duration} seconds.")

            await self.announcement.announce(self.game_timer, "Enemy glyph activated. Cooldown started.")
            logger.info(f"Glyph cooldown started in guild ID {self.game_timer.guild_id}.")

            # Announce 1-minute warning
            await asyncio.sleep(cooldown_duration - 60)
            if not self.is_running:
                logger.info(f"GlyphTimer stopped before 1-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph available in 1 minute!")
            logger.info(f"1-minute warning for Glyph cooldown in guild ID {self.game_timer.guild_id}.")

            # Final announcement
            await asyncio.sleep(60)
            if not self.is_running:
                logger.info(f"GlyphTimer stopped before final availability announcement for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph is now available!")
            logger.info(f"Glyph is now available in guild ID {self.game_timer.guild_id}.")

        except asyncio.CancelledError:
            logger.info(f"GlyphTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"GlyphTimer concluded for guild ID {self.game_timer.guild_id}.")
