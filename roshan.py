import asyncio
import logging

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""

    def __init__(self, game_timer):
        self.is_active = False
        self.game_timer = game_timer  # Store the GameTimer instance

    async def start(self, channel):
        """Start the Roshan respawn timer with TTS announcements."""
        if self.is_active:
            await channel.send("Roshan timer is already active.")
            await self.game_timer.announce_message("Roshan timer is already active.")
            logging.warning("Roshan timer is already active.")
            return

        self.is_active = True
        await channel.send("Roshan has been killed! Starting respawn timer.")
        await self.game_timer.announce_message("Roshan has been killed! Starting respawn timer.")
        logging.info("Roshan timer started.")

        # Roshan respawn time is between 8 to 11 minutes
        min_respawn = 8 * 60  # 8 minutes in seconds
        max_respawn = 11 * 60  # 11 minutes in seconds

        # Notify at minimum respawn time
        await asyncio.sleep(min_respawn - 60)  # Notify 1 minute before
        await channel.send("Roshan may respawn in 1 minute!")
        await self.game_timer.announce_message("Roshan may respawn in 1 minute!")
        logging.info("Roshan may respawn in 1 minute.")

        await asyncio.sleep(60)
        await channel.send("Roshan may have respawned!")
        await self.game_timer.announce_message("Roshan may have respawned!")
        logging.info("Roshan may have respawned.")

        # Notify at maximum respawn time
        await asyncio.sleep(max_respawn - min_respawn)
        await channel.send("Roshan has definitely respawned!")
        await self.game_timer.announce_message("Roshan has definitely respawned!")
        logging.info("Roshan has definitely respawned.")
        self.is_active = False
