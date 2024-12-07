# src/timers/roshan.py

import asyncio
from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger

class RoshanTimer(BaseTimer):
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"RoshanTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel):
        logger.info(f"RoshanTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            if self.game_timer.mode == 'turbo':
                min_respawn = 4 * 60  # Turbo mode: 4 minutes minimum respawn
                max_respawn = 5.5 * 60  # Turbo mode: 5.5 minutes max respawn
                logger.debug(f"Turbo mode: Roshan respawn between {min_respawn} and {max_respawn} seconds.")
            else:
                min_respawn = 8 * 60  # Regular mode: 8 minutes minimum respawn
                max_respawn = 11 * 60  # Regular mode: 11 minutes max respawn
                logger.debug(f"Regular mode: Roshan respawn between {min_respawn} and {max_respawn} seconds.")

            # Announce Roshan killed
            await self.announcement.announce(self.game_timer, "Roshan killed!")
            logger.info(f"Roshan killed in guild ID {self.game_timer.guild_id}. Starting respawn timer.")

            # Calculate game time and respawn window
            current_game_time_seconds = self.game_timer.time_elapsed
            current_game_minutes = current_game_time_seconds // 60
            min_respawn_minutes = current_game_minutes + (min_respawn // 60)
            max_respawn_minutes = current_game_minutes + (max_respawn // 60)

            # Announce respawn window after 1 second
            await self.sleep_with_pause(1)
            await self.announcement.announce(
                self.game_timer,
                f"Roshan possible from: {min_respawn_minutes} to {max_respawn_minutes} minute."
            )
            logger.info(
                f"Announced Roshan respawn window: {min_respawn_minutes} to {max_respawn_minutes} minutes for guild ID {self.game_timer.guild_id}."
            )

            # Announce 5-minute warning
            await self.sleep_with_pause(min_respawn - 300)
            if not self.is_running:
                logger.info(f"RoshanTimer stopped before 5-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 5 minutes!")
            logger.info(f"5-minute warning for Roshan respawn in guild ID {self.game_timer.guild_id}.")

            # Announce 3-minute warning
            await self.sleep_with_pause(120)
            if not self.is_running:
                logger.info(f"RoshanTimer stopped before 3-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 3 minutes!")
            logger.info(f"3-minute warning for Roshan respawn in guild ID {self.game_timer.guild_id}.")

            # Announce 1-minute warning
            await self.sleep_with_pause(120)
            if not self.is_running:
                logger.info(f"RoshanTimer stopped before 1-minute warning for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 1 minute!")
            logger.info(f"1-minute warning for Roshan respawn in guild ID {self.game_timer.guild_id}.")

            # Final announcement before max respawn
            await self.sleep_with_pause(60)
            if not self.is_running:
                logger.info(
                    f"RoshanTimer stopped before final respawn announcement for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Roshan may be up!")
            logger.info(f"Final warning before Roshan respawn in guild ID {self.game_timer.guild_id}.")

            # Wait for the remaining time until max respawn
            await self.sleep_with_pause(max_respawn - min_respawn)
            if not self.is_running:
                logger.info(
                    f"RoshanTimer stopped before final respawn announcement for guild ID {self.game_timer.guild_id}.")
                return
            await self.announcement.announce(self.game_timer, "Roshan is up for sure!")
            logger.info(f"Roshan has respawned in guild ID {self.game_timer.guild_id}.")

        except asyncio.CancelledError:
            logger.info(f"RoshanTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"RoshanTimer concluded for guild ID {self.game_timer.guild_id}.")
