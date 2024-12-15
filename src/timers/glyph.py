import asyncio

from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger


class GlyphTimer(BaseTimer):
    """
    Handles the Glyph cooldown timer for a Discord guild.

    This timer announces the activation of an enemy glyph and manages cooldown warnings
    leading up to the glyph's availability.
    """

    def __init__(self, game_timer):
        """
        Initialize the GlyphTimer with the associated game timer.

        Args:
            game_timer: An instance containing game state and timer-related information.
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        logger.debug(f"GlyphTimer initialized for guild ID {self.game_timer.guild_id}.")

    async def _run_timer(self, channel: any) -> None:
        """
        Execute the Glyph cooldown countdown and send appropriate announcements.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        try:
            logger.info(f"GlyphTimer running for guild ID {self.game_timer.guild_id}.")

            # Determine cooldown duration based on game mode
            cooldown_duration = 5 * 60 if self.game_timer.mode == 'regular' else 3 * 60
            logger.debug(f"Cooldown duration set to {cooldown_duration} seconds.")

            # Announce the start of the glyph cooldown
            await self.announcement.announce(self.game_timer, "Enemy glyph activated. Cooldown started.")
            logger.info(f"Glyph cooldown started for guild ID {self.game_timer.guild_id}.")

            # Define warnings leading up to glyph availability
            warnings = [
                (cooldown_duration - 60, "Enemy glyph available in 1 minute!"),
                (60, "Enemy glyph is now available!")
            ]

            # Schedule the warnings
            await self.schedule_warnings(warnings, self.announcement)

        except asyncio.CancelledError:
            logger.info(f"GlyphTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"GlyphTimer concluded for guild ID {self.game_timer.guild_id}.")
