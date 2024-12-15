# src/timers/tormentor.py

import asyncio

from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger


class TormentorTimer(BaseTimer):
    """Class to handle the Tormentor respawn timer."""

    def __init__(self, game_timer):
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"TormentorTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel):
        logger.info(f"TormentorTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            # Determine the full respawn duration based on mode
            if self.game_timer.mode == 'regular':
                respawn_duration = 10 * 60  # 10 minutes
            else:
                respawn_duration = 5 * 60   # 5 minutes

            await self.announcement.announce(self.game_timer, "Tormentor timer started.")
            logger.info(f"Tormentor timer started for guild ID {self.game_timer.guild_id}.")

            # Schedule warnings:
            #  - 3-minute warning at (respawn_duration - 180)
            #  - 1-minute warning at 120 seconds later
            #  - final announcement after another 60 seconds
            warnings = [
                (respawn_duration - 180, "Tormentor will respawn in 3 minutes!"),
                (120,                    "Tormentor will respawn in 1 minute!"),
                (60,                     "Tormentor has respawned!")
            ]

            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"TormentorTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"TormentorTimer concluded for guild ID {self.game_timer.guild_id}.")
