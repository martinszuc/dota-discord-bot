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
        try:
            logger.info(f"TormentorTimer running for guild ID {self.game_timer.guild_id}.")
            # Set respawn duration based on game mode
            if self.game_timer.mode == 'regular':
                respawn_duration = 10 * 60  # 10 minutes for regular
                logger.debug(f"Regular mode: Tormentor respawn in {respawn_duration} seconds.")
            else:
                respawn_duration = 5 * 60  # 5 minutes for turbo
                logger.debug(f"Turbo mode: Tormentor respawn in {respawn_duration} seconds.")

            await self.announcement.announce(self.game_timer, "Tormentor timer started.")
            logger.info(f"Tormentor timer started for guild ID {self.game_timer.guild_id}.")

            # Announce 3-minute warning
            await asyncio.sleep(respawn_duration - 180)
            if not self.is_running:
                logger.info(f"TormentorTimer stopped before 3-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Tormentor will respawn in 3 minutes!")
            logger.info(f"3-minute warning for Tormentor timer in guild ID {self.game_timer.guild_id}.")

            # Announce 1-minute warning
            await asyncio.sleep(120)
            if not self.is_running:
                logger.info(f"TormentorTimer stopped before 1-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Tormentor will respawn in 1 minute!")
            logger.info(f"1-minute warning for Tormentor timer in guild ID {self.game_timer.guild_id}.")

            # Final announcement
            await asyncio.sleep(60)
            if not self.is_running:
                logger.info(f"TormentorTimer stopped before final respawn announcement for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Tormentor has respawned!")
            logger.info(f"Tormentor has respawned in guild ID {self.game_timer.guild_id}.")

        except asyncio.CancelledError:
            logger.info(f"TormentorTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"TormentorTimer concluded for guild ID {self.game_timer.guild_id}.")
