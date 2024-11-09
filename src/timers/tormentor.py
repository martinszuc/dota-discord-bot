# src/timers/tormentor.py

import asyncio
import logging
from communication import Announcement

class TormentorTimer:
    """Class to handle the Tormentor respawn timer."""

    def __init__(self, game_timer):
        self.game_timer = game_timer
        self.logger = logging.getLogger('DotaDiscordBot')
        self.task = None
        self.is_running = False
        self.announcement = Announcement()  # Initialize the Announcement instance

    async def start(self, channel):
        """Start the Tormentor respawn timer."""
        if self.is_running:
            await self.announcement.announce(self.game_timer, "Tormentor timer is already running.")
            self.logger.warning("Attempted to start Tormentor timer, but it is already running.")
            return
        self.is_running = True
        self.logger.info("Tormentor timer started.")
        await self.announcement.announce(self.game_timer, "Tormentor has been killed!.")
        self.task = asyncio.create_task(self._run_timer(channel))

    async def _run_timer(self, channel):
        """Internal method to run the Tormentor respawn timer."""
        try:
            await asyncio.sleep(600)  # 10 minutes
            await self.announcement.announce(self.game_timer, "Tormentor has respawned!")
            self.logger.info("Tormentor has respawned.")
            self.is_running = False
        except asyncio.CancelledError:
            self.logger.info("Tormentor timer was cancelled.")
            await self.announcement.announce(self.game_timer, "Tormentor respawn timer has been cancelled.")
            self.is_running = False

    async def cancel(self):
        """Cancel the Tormentor respawn timer."""
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                self.logger.info("Tormentor timer task was successfully cancelled.")
            await self.announcement.announce(self.game_timer, "Tormentor respawn timer has been cancelled.")
            self.logger.info("Tormentor timer cancelled.")
            self.is_running = False
        else:
            self.logger.warning("Attempted to cancel Tormentor timer, but it was not running.")
