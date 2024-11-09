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

    async def _run_timer(self, channel):
        try:
            # Set cooldown duration based on game mode
            cooldown_duration = 5 * 60 if self.game_timer.mode == 'regular' else 5 * 60  # 5 minutes for regular, 3 minutes for turbo

            await self.announcement.announce(self.game_timer, "Enemy glyph activated. Cooldown started.")
            await asyncio.sleep(cooldown_duration - 60)  # Announce 1-minute warning

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph available in 1 minute!")

            await asyncio.sleep(60)  # Wait the remaining 1 minute

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph is now available!")

        except asyncio.CancelledError:
            logger.info("Glyph timer cancelled.")
        finally:
            self.is_running = False
