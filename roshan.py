# roshan.py

import asyncio
import logging

logger = logging.getLogger(__name__)

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        self.is_active = False
        self.game_timer = game_timer

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

        min_respawn = 8 * 60
        max_respawn = 11 * 60

        await asyncio.sleep(min_respawn - 60)
        await channel.send("Roshan may respawn in 1 minute!", tts=True)
        await self.game_timer.announce_message("Roshan may respawn in 1 minute!")
        logger.info("Roshan may respawn in 1 minute.")

        await asyncio.sleep(60)
        await channel.send("Roshan may have respawned!", tts=True)
        await self.game_timer.announce_message("Roshan may have respawned!")
        logger.info("Roshan may have respawned.")

        await asyncio.sleep(max_respawn - min_respawn)
        await channel.send("Roshan has definitely respawned!", tts=True)
        await self.game_timer.announce_message("Roshan has definitely respawned!")
        logger.info("Roshan has definitely respawned.")
        self.is_active = False
