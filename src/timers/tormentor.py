# src/timers/tormentor.py

import asyncio
import logging


class TormentorTimer:
    """Class to handle the Tormentor respawn timer."""

    def __init__(self, game_timer):
        self.game_timer = game_timer
        self.logger = logging.getLogger('DotaDiscordBot')
        self.task = None
        self.is_running = False

    async def start(self, channel):
        """Start the Tormentor respawn timer."""
        if self.is_running:
            await channel.send("Tormentor timer is already running.", tts=True)
            self.logger.warning("Attempted to start Tormentor timer, but it is already running.")
            return
        self.is_running = True
        self.logger.info("Tormentor timer started.")
        await channel.send("Tormentor has been killed! Respawn timer started for 10 minutes.", tts=True)
        self.task = asyncio.create_task(self._run_timer(channel))

    async def _run_timer(self, channel):
        """Internal method to run the Tormentor respawn timer."""
        try:
            await asyncio.sleep(600)  # 10 minutes
            await channel.send("Tormentor has respawned!", tts=True)
            self.logger.info("Tormentor has respawned.")
            self.is_running = False
        except asyncio.CancelledError:
            self.logger.info("Tormentor timer was cancelled.")
            await channel.send("Tormentor respawn timer has been cancelled.", tts=True)
            self.is_running = False

    async def cancel(self):
        """Cancel the Tormentor respawn timer."""
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.logger.info("Tormentor timer cancelled.")
        else:
            self.logger.warning("Attempted to cancel Tormentor timer, but it was not running.")
