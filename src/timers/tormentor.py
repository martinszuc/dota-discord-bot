import asyncio

from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger


class TormentorTimer(BaseTimer):
    """
    Handles the Tormentor respawn timer for a Discord guild.

    This timer announces the start of Tormentor's respawn countdown and schedules warnings
    leading up to Tormentor's availability based on the game mode.
    """

    def __init__(self, game_timer):
        """
        Initialize the TormentorTimer with the associated game timer.

        Args:
            game_timer: An instance containing game state and timer-related information.
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"TormentorTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel: any) -> None:
        """
        Execute the Tormentor respawn countdown and send appropriate announcements.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        logger.info(f"TormentorTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            # Determine respawn duration based on game mode
            if self.game_timer.mode == 'regular':
                respawn_duration = 10 * 60  # 10 minutes
            else:
                respawn_duration = 5 * 60   # 5 minutes

            logger.debug(f"TormentorTimer set with respawn_duration={respawn_duration} seconds.")

            # Announce the start of the Tormentor timer
            await self.announcement.announce(self.game_timer, "Tormentor timer started.")
            logger.info(f"Tormentor timer started for guild ID {self.game_timer.guild_id}.")

            # Define warnings leading up to Tormentor's respawn
            warnings = [
                (respawn_duration - 180, "Tormentor will respawn in 3 minutes!"),
                (120,                    "Tormentor will respawn in 1 minute!"),
                (60,                     "Tormentor has respawned!")
            ]

            # Schedule the warnings
            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"TormentorTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"TormentorTimer concluded for guild ID {self.game_timer.guild_id}.")
