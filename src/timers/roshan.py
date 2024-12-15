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
                min_respawn = 4 * 60   # 4 minutes
                max_respawn = 5.5 * 60 # 5.5 minutes
            else:
                min_respawn = 8 * 60   # 8 minutes
                max_respawn = 11 * 60  # 11 minutes

            # Instead of "Roshan killed!", clarify that the user triggered a Roshan timer
            await self.announcement.announce(self.game_timer, "Roshan timer started.")
            logger.info(f"Roshan timer started for guild ID {self.game_timer.guild_id}. Respawn window: {min_respawn} - {max_respawn} seconds.")

            # Wait 1 second and then post the possible respawn window
            await self.sleep_with_pause(1)
            current_game_time_seconds = self.game_timer.time_elapsed
            current_game_minutes = current_game_time_seconds // 60
            min_respawn_minutes = current_game_minutes + (min_respawn // 60)
            max_respawn_minutes = current_game_minutes + (max_respawn // 60)

            await self.announcement.announce(
                self.game_timer,
                f"Roshan can respawn between minute {min_respawn_minutes} and {max_respawn_minutes}."
            )

            # 5-min warning
            await self.sleep_with_pause(min_respawn - 300)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 5 minutes!")

            # 3-min warning
            await self.sleep_with_pause(120)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 3 minutes!")

            # 1-min warning
            await self.sleep_with_pause(120)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 1 minute!")

            # Final announcement at min_respawn
            await self.sleep_with_pause(60)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may be up now!")

            # Wait the difference up to max_respawn
            await self.sleep_with_pause(max_respawn - min_respawn)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan is definitely up now!")

        except asyncio.CancelledError:
            logger.info(f"RoshanTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"RoshanTimer concluded for guild ID {self.game_timer.guild_id}.")
