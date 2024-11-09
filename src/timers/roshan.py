import asyncio
from src.utils.config import logger

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        self.is_active = False
        self.game_timer = game_timer
        self.task = None

    async def start(self, channel):
        """Start the Roshan respawn timer with TTS announcements."""
        if self.is_active:
            await channel.send("Roshan timer is already active.", tts=True)
            await self.game_timer.announce_message("Roshan timer is already active.")
            logger.warning("Roshan timer is already active.")
            return

        self.is_active = True
        await channel.send("Roshan has been killed! Starting respawn timer.", tts=True)
        await self.game_timer.announce_message("Roshan has been killed! Starting respawn timer.")
        logger.info("Roshan timer started.")

        # Run the timer in an asynchronous task
        self.task = asyncio.create_task(self.run_timer(channel))

    async def run_timer(self, channel):
        try:
            min_respawn = 8 * 60  # 8 minutes
            max_respawn = 11 * 60  # 11 minutes

            # Warning at min_respawn - 60 seconds
            await asyncio.sleep(min_respawn - 60)
            message = "Roshan may respawn in 1 minute!"
            await channel.send(message)
            await self.game_timer.announce_message(message)
            logger.info("Roshan may respawn in 1 minute.")

            # Roshan may have respawned
            await asyncio.sleep(60)
            message = "Roshan may have respawned!"
            await channel.send(message)
            await self.game_timer.announce_message(message)
            logger.info("Roshan may have respawned.")

            # Definitive respawn
            await asyncio.sleep(max_respawn - min_respawn)
            message = "Roshan has definitely respawned!"
            await channel.send(message)
            await self.game_timer.announce_message(message)
            logger.info("Roshan has definitely respawned.")

        except asyncio.CancelledError:
            logger.info("Roshan timer was cancelled.")
            await channel.send("Roshan timer has been cancelled.", tts=True)
            await self.game_timer.announce_message("Roshan timer has been cancelled.")
        finally:
            self.is_active = False
            self.task = None

    async def cancel(self):
        """Cancel the Roshan respawn timer."""
        if self.is_active:
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info("Roshan timer task was successfully cancelled.")
            self.is_active = False
            self.task = None
            logger.info("Roshan timer has been reset and is inactive.")
        else:
            logger.info("Roshan timer was not active.")
