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
                min_respawn = 4 * 60    # 4 minutes
                max_respawn = 5.5 * 60  # 5.5 minutes
            else:
                min_respawn = 8 * 60    # 8 minutes
                max_respawn = 11 * 60   # 11 minutes

            # Start message
            await self.announcement.announce(self.game_timer, "Roshan timer started.")
            logger.info(f"Roshan timer started for guild ID {self.game_timer.guild_id}.")

            # Slight delay before announcing the window
            await self.sleep_with_pause(1)

            # Calculate possible respawn window
            max_respawn_minutes, min_respawn_minutes = await self.calc_respawn_time(max_respawn, min_respawn)

            await self.announcement.announce(
                self.game_timer,
                f"Next roshan between minute {min_respawn_minutes} and {max_respawn_minutes}."
            )

            # Combine all warnings into a single list
            warnings = [
                (min_respawn - 300, "Roshan may respawn in 5 minutes!"),
                (120,               "Roshan may respawn in 3 minutes!"),
                (120,               "Roshan may respawn in 1 minute!"),
                (60,                "Roshan may be up now!"),
                ((max_respawn - min_respawn), "Roshan is definitely up now!")
            ]

            # Use the new helper method from BaseTimer
            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"RoshanTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"RoshanTimer concluded for guild ID {self.game_timer.guild_id}.")

    async def calc_respawn_time(self, max_respawn, min_respawn):
        current_game_time_seconds = self.game_timer.time_elapsed
        current_game_minutes = current_game_time_seconds // 60
        # Convert min_respawn and max_respawn to integer minutes
        min_respawn_minutes = int(current_game_minutes + (min_respawn / 60))
        max_respawn_minutes = int(current_game_minutes + (max_respawn / 60))
        return max_respawn_minutes, min_respawn_minutes
