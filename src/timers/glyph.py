import asyncio

from ..utils.config import logger


class GlyphTimer:
    """Class to manage the Glyph cooldown timer."""

    def __init__(self, game_timer):
        self.is_active = False
        self.game_timer = game_timer
        self.task = None

    async def start(self, channel):
        """Start the Glyph cooldown timer with TTS announcements."""
        if self.task:
            await self.cancel()

        self.is_active = True
        await channel.send("Enemy glyph used! Starting 5-minute cooldown timer.")
        await self.game_timer.announce_message("Enemy glyph used! Starting 5-minute cooldown timer.")
        logger.info("Glyph timer started.")

        # Start the cooldown timer task
        self.task = asyncio.create_task(self.run_timer(channel))

    async def run_timer(self, channel):
        """Run the Glyph cooldown timer and announce when it's ready."""
        try:
            cooldown_duration = 5 * 60  # 5 minutes

            # Sleep for the cooldown period
            await asyncio.sleep(cooldown_duration)
            if not self.is_active:
                return
            await self._announce(channel, "Glyph is now available!")

        except asyncio.CancelledError:
            logger.info("Glyph timer was cancelled.")
            await self._announce(channel, "Glyph timer has been cancelled.")
        finally:
            # Reset after completion or cancellation
            self.is_active = False
            self.task = None

    async def cancel(self):
        """Cancel the Glyph cooldown timer."""
        if self.is_active:
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info("Glyph timer task was successfully cancelled.")
            self.is_active = False
            self.task = None  # Reset task reference
            logger.info("Glyph timer has been set to inactive.")
        else:
            logger.info("Glyph timer was not active.")

    async def _announce(self, channel, message):
        """Helper function to send TTS announcements."""
        await channel.send(message)
        await self.game_timer.announce_message(message)
        logger.info(message)