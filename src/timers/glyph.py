import asyncio
from src.utils.config import logger
from communication import Announcement

class GlyphTimer:
    """Class to manage the Glyph cooldown timer."""

    def __init__(self, game_timer):
        self.is_active = False
        self.game_timer = game_timer
        self.task = None
        self.announcement = Announcement()

    async def start(self, channel):
        """Start the Glyph cooldown timer with TTS announcements."""
        if self.is_active:
            await self.announcement.announce(self.game_timer, "Glyph timer is already active.")
            logger.warning("Glyph timer is already active.")
            return

        self.is_active = True
        await self.announcement.announce(self.game_timer, "Enemy glyph used! Starting 5-minute cooldown timer.")
        logger.info("Glyph timer started.")

        # Start the cooldown timer task
        self.task = asyncio.create_task(self.run_timer(channel))

    async def run_timer(self, channel):
        """Run the Glyph cooldown timer and announce when it's ready."""
        try:
            glyph_cooldown = 5 * 60  # 5 minutes

            # Announce when 30 seconds are left
            await asyncio.sleep(glyph_cooldown - 30)
            if not self.is_active:
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph available in 30 seconds!")

            # Announce when cooldown ends
            await asyncio.sleep(30)
            if not self.is_active:
                return
            await self.announcement.announce(self.game_timer, "Enemy glyph cooldown has ended!")

            logger.info("Enemy glyph cooldown ended.")

        except asyncio.CancelledError:
            logger.info("Glyph timer was cancelled.")
            await self.announcement.announce(self.game_timer, "Glyph timer has been cancelled.")
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
            self.task = None
            await self.announcement.announce(self.game_timer, "Glyph timer has been reset and is inactive.")
            logger.info("Glyph timer has been reset and is inactive.")
        else:
            logger.info("Glyph timer was not active.")
