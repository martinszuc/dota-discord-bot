# src/timers/tormentor.py

import asyncio
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
            # Set respawn duration based on game mode
            respawn_duration = 10 * 60 if self.game_timer.mode == 'regular' else 5 * 60  # 10 minutes for regular,  minutes for turbo

            await self.announcement.announce(self.game_timer, "Tormentor defeated! Respawn timer started.")
            await asyncio.sleep(respawn_duration - 60)  # Announce 1-minute warning

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Tormentor will respawn in 1 minute!")

            await asyncio.sleep(60)  # Wait the remaining 1 minute

            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Tormentor has respawned!")

        except asyncio.CancelledError:
            logger.info("Tormentor timer cancelled.")
        finally:
            self.is_running = False
