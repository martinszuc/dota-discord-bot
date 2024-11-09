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
            if self.game_timer.mode == 'turbo':
                min_respawn = 4 * 60  # Turbo mode: 4 minutes minimum respawn
                max_respawn = 5.5 * 60  # Turbo mode: 5.5 minutes max respawn
            else:
                min_respawn = 8 * 60  # Regular mode: 8 minutes minimum respawn
                max_respawn = 11 * 60  # Regular mode: 11 minutes max respawn

            await self.announcement.announce(self.game_timer, "Roshan killed!")
            await asyncio.sleep(min_respawn - 60)  # Warning 1 minute before min respawn

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 1 minute!")

            await asyncio.sleep(60)  # 1 minute

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may be up!")

            await asyncio.sleep(max_respawn - min_respawn)  # Additional time to max respawn

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan is up!")

        except asyncio.CancelledError:
            logger.info("Roshan timer cancelled.")
        finally:
            self.is_running = False
