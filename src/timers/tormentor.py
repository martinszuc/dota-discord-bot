# src/timers/tormentor.py

import asyncio
import logging
from communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger

class TormentorTimer(BaseTimer):
    """Class to handle the Tormentor respawn timer."""

    def __init__(self, game_timer):
        super().__init__(game_timer)
        self.announcement = Announcement()

    async def _run_timer(self, channel):
        try:
            await self.announcement.announce(self.game_timer, "Tormentor killed! Respawn timer started.")
            await asyncio.sleep(10 * 60)  # 10 minutes

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Tormentor has respawned!")

        except asyncio.CancelledError:
            logger.info("Tormentor timer cancelled.")
            await self.announcement.announce(self.game_timer, "Tormentor timer cancelled.")
        finally:
            self.is_running = False
