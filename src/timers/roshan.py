import asyncio

from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger


class RoshanTimer(BaseTimer):
    """
    Manages Roshan's respawn timer in a Discord guild.

    This timer announces the start of Roshan's respawn and schedules warnings leading
    up to Roshan's availability based on the game mode.
    """

    def __init__(self, game_timer):
        """
        Initialize the RoshanTimer with the associated game timer.

        Args:
            game_timer: An instance containing game state and timer-related information.
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"RoshanTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel: any) -> None:
        """
        Execute the Roshan respawn countdown and send appropriate announcements.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        logger.info(f"RoshanTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            # Determine respawn duration based on game mode
            if self.game_timer.mode == 'turbo':
                min_respawn = 4 * 60    # 4 minutes
                max_respawn = 5.5 * 60  # 5.5 minutes
            else:
                min_respawn = 8 * 60    # 8 minutes
                max_respawn = 11 * 60   # 11 minutes

            logger.debug(f"RoshanTimer set with min_respawn={min_respawn} seconds and max_respawn={max_respawn} seconds.")

            # Announce the start of the Roshan timer
            await self.announcement.announce(self.game_timer, "Roshan timer started.")
            logger.info(f"Roshan timer started for guild ID {self.game_timer.guild_id}.")

            # Short delay before announcing the respawn window
            await self.sleep_with_pause(1)

            # Calculate respawn window in minutes
            max_respawn_minutes, min_respawn_minutes = self.calc_respawn_time(max_respawn, min_respawn)
            respawn_window_message = (
                f"Next Roshan between minute {min_respawn_minutes} and {max_respawn_minutes}."
            )
            await self.announcement.announce(self.game_timer, respawn_window_message)
            logger.info(f"Announced Roshan respawn window: '{respawn_window_message}'")

            # Define warnings leading up to Roshan's respawn
            warnings = [
                (min_respawn - 300, "Roshan may respawn in 5 minutes!"),
                (120,               "Roshan may respawn in 3 minutes!"),
                (120,               "Roshan may respawn in 1 minute!"),
                (60,                "Roshan may be up now!"),
                ((max_respawn - min_respawn), "Roshan is definitely up now!")
            ]

            # Schedule the warnings
            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"RoshanTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"RoshanTimer concluded for guild ID {self.game_timer.guild_id}.")

    def calc_respawn_time(self, max_respawn: float, min_respawn: float) -> tuple:
        """
        Calculate the respawn time window in minutes based on elapsed game time.

        Args:
            max_respawn (float): The maximum respawn time in seconds.
            min_respawn (float): The minimum respawn time in seconds.

        Returns:
            tuple: A tuple containing (max_respawn_minutes, min_respawn_minutes).
        """
        current_game_time_seconds = self.game_timer.time_elapsed
        current_game_minutes = current_game_time_seconds // 60
        min_respawn_minutes = int(current_game_minutes + (min_respawn // 60))
        max_respawn_minutes = int(current_game_minutes + (max_respawn // 60))
        logger.debug(f"Calculated respawn time window: {min_respawn_minutes}-{max_respawn_minutes} minutes.")
        return max_respawn_minutes, min_respawn_minutes
