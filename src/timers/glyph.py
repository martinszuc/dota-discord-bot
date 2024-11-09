# src/timers/glyph.py

import asyncio
import logging
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
            await self.announcement.announce(self.game_timer, "Enemy glyph pressed. 5 minutes cooldown.")
            await asyncio.sleep(5 * 60)  # 5-minute cooldown

            while self.is_running:
                await self.pause_event.wait()  # Wait if paused
                if not self.is_running:
                    break
                await self.announcement.announce(self.game_timer, "Enemy glyph now available!")
                break
        except asyncio.CancelledError:
            logger.info("Glyph timer cancelled.")
        finally:
            self.is_running = False
