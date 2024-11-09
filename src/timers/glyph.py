# src/timers/glyph.py

import asyncio
import logging
from communication import Announcement

class GlyphTimer:
    """Class to handle the Glyph cooldown timer."""

    def __init__(self, game_timer):
        self.is_running = False  # Ensure this attribute exists
        self.game_timer = game_timer
        self.task = None
        self.logger = logging.getLogger('DotaDiscordBot')
        self.announcement = Announcement()

    async def start(self, channel):
        """Start the Glyph cooldown timer."""
        if self.is_running:
            await self.announcement.announce(self.game_timer, "Glyph timer is already running.")
            self.logger.warning("Attempted to start Glyph timer, but it is already running.")
            return
        self.is_running = True
        await self.announcement.announce(self.game_timer, "Glyph used! Cooldown timer started for 5 minutes.")
        self.logger.info("Glyph timer started.")
        self.task = asyncio.create_task(self.run_timer(channel))

    async def run_timer(self, channel):
        """Run the Glyph cooldown timer."""
        try:
            await asyncio.sleep(300)  # 5 minutes
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Glyph cooldown has ended!")
            self.logger.info("Glyph cooldown ended.")
        except asyncio.CancelledError:
            self.logger.info("Glyph timer was cancelled.")
            await self.announcement.announce(self.game_timer, "Glyph timer has been cancelled.")
        finally:
            self.is_running = False
            self.task = None

    async def cancel(self):
        """Cancel the Glyph cooldown timer."""
        if self.is_running:
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    self.logger.info("Glyph timer task was successfully cancelled.")
            self.is_running = False
            self.task = None
            await self.announcement.announce(self.game_timer, "Glyph timer has been reset and is inactive.")
            self.logger.info("Glyph timer has been reset and is inactive.")
        else:
            self.logger.info("Glyph timer was not active.")
