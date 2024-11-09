# src/timers/roshan.py

import asyncio
import logging
from communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger

class RoshanTimer(BaseTimer):
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        super().__init__(game_timer)
        self.announcement = Announcement()

    async def _run_timer(self, channel):
        try:
            min_respawn = 8 * 60  # 8 minutes
            max_respawn = 11 * 60  # 11 minutes

            await self.announcement.announce(self.game_timer, "Roshan killed! Respawn timer started.")
            await asyncio.sleep(min_respawn - 60)  # 7 minutes

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 1 minute!")

            await asyncio.sleep(60)  # 1 minute

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may have respawned!")

            await asyncio.sleep(max_respawn - min_respawn)  # Additional 4 minutes

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan has respawned!")

        except asyncio.CancelledError:
            logger.info("Roshan timer cancelled.")
            await self.announcement.announce(self.game_timer, "Roshan timer cancelled.")
        finally:
            self.is_running = False
