# src/timers/roshan.py

import asyncio
from src.utils.config import logger
from communication import Announcement

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        self.is_running = False  # Renamed from is_active
        self.game_timer = game_timer
        self.task = None
        self.announcement = Announcement()

    async def start(self, channel):
        """Start the Roshan respawn timer with announcements."""
        if self.is_running:
            await self.announcement.announce(self.game_timer, "Roshan timer active.")
            logger.warning("Roshan timer is already active.")
            return

        self.is_running = True
        await self.announcement.announce(self.game_timer, "Roshan killed! .")
        logger.info("Roshan timer started.")

        # Start the timer task
        self.task = asyncio.create_task(self.run_timer(channel))

    async def run_timer(self, channel):
        """Run the Roshan respawn timer and announce at key intervals."""
        try:
            min_respawn = 8 * 60  # 8 minutes
            max_respawn = 11 * 60  # 11 minutes

            # Warning at min_respawn - 60 seconds
            await asyncio.sleep(min_respawn - 60)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan may respawn in 1 minute!")

            # Roshan may have respawned
            await asyncio.sleep(60)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan maybe up!")

            # Definitive respawn
            await asyncio.sleep(max_respawn - min_respawn)
            if not self.is_running:
                return
            await self.announcement.announce(self.game_timer, "Roshan up!")

        except asyncio.CancelledError:
            logger.info("Roshan timer was cancelled.")
            await self.announcement.announce(self.game_timer, "Roshan timer cancelled.")
        finally:
            # Reset after completion or cancellation
            self.is_running = False
            self.task = None

    async def cancel(self):
        """Cancel the Roshan respawn timer."""
        if self.is_running:
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info("Roshan timer task was successfully cancelled.")
            self.is_running = False
            self.task = None
            await self.announcement.announce(self.game_timer, "Roshan timer has been reset and is inactive.")
            logger.info("Roshan timer has been reset and is inactive.")
        else:
            logger.info("Roshan timer was not active.")
