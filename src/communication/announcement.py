import asyncio

import discord

from src.managers.tts_manager import TTSManager
from src.utils.config import logger


class Announcement:
    """
    Manages TTS announcements in voice channels for a Discord server.

    This class handles queuing messages for TTS playback in voice channels via a queue system.
    """

    def __init__(self):
        """
        Initialize the Announcement manager.

        Sets up the TTS manager, message queue, and initializes consumer task state.
        """
        self.tts_manager = TTSManager()
        self.queue = asyncio.Queue()
        self.consumer_task = None
        self._consumer_running = False

    async def announce(self, game_timer, message: str):
        """
        Announce a message via TTS in the voice channel.

        Queues the message for TTS playback if the voice client is connected.

        Args:
            game_timer: An instance containing game state and channel information.
            message (str): The message to announce via TTS.
        """
        # Check if the voice client is connected before queuing the TTS message
        if game_timer.voice_client and game_timer.voice_client.is_connected():
            await self.queue.put((game_timer, message))
            # Start the consumer task if it's not already running
            if not self._consumer_running:
                self._consumer_running = True
                self.consumer_task = asyncio.create_task(self._message_consumer())
        else:
            logger.warning("Voice client is not connected; cannot announce message.")

    async def _message_consumer(self):
        """
        Continuously process messages from the queue and play them in the voice channel.

        This coroutine runs as a background task, ensuring that TTS messages are
        played sequentially without overlapping.
        """
        try:
            while True:
                game_timer, msg = await self.queue.get()
                if game_timer.voice_client and game_timer.voice_client.is_connected():
                    try:
                        await self.tts_manager.play_tts(game_timer.voice_client, msg)
                        logger.info(f"Played TTS message in voice channel: {msg}")
                    except Exception as e:
                        logger.error(f"Error during voice announcement: {e}", exc_info=True)
                else:
                    logger.warning("Voice client disconnected while processing queue.")
                # Indicate that the queued task is done
                self.queue.task_done()
        except asyncio.CancelledError:
            logger.info("Message consumer task cancelled")
        finally:
            self._consumer_running = False
            logger.debug("Message consumer has stopped running.")
