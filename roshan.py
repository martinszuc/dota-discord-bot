import asyncio
import logging

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""

    def __init__(self):
        self.is_active = False

    async def start(self, channel):
        """Start the Roshan respawn timer."""
        if self.is_active:
            await channel.send("Roshan timer is already active.", tts=True)
            logging.warning("Roshan timer is already active.")
            return

        self.is_active = True
        await channel.send("Roshan has been killed! Starting respawn timer.", tts=True)
        logging.info("Roshan timer started.")

        # Roshan respawn time is between 8 to 11 minutes
        min_respawn = 8 * 60  # 8 minutes in seconds
        max_respawn = 11 * 60  # 11 minutes in seconds

        # Notify at minimum respawn time
        await asyncio.sleep(min_respawn - 60)  # Notify 1 minute before
        await channel.send("Roshan may respawn in 1 minute!", tts=True)
        logging.info("Roshan may respawn in 1 minute.")

        await asyncio.sleep(60)
        await channel.send("Roshan may have respawned!", tts=True)
        logging.info("Roshan may have respawned.")

        # Notify at maximum respawn time
        await asyncio.sleep(max_respawn - min_respawn)
        await channel.send("Roshan has definitely respawned!", tts=True)
        logging.info("Roshan has definitely respawned.")
        self.is_active = False
