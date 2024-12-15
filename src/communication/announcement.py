import discord
import asyncio
from src.managers.tts_manager import TTSManager
from src.utils.config import logger

class Announcement:
    """A class to manage announcements in text and voice channels."""

    def __init__(self):
        self.tts_manager = TTSManager()
        self.queue = asyncio.Queue()
        self.consumer_task = None
        self._consumer_running = False

    async def announce(self, game_timer, message):
        """
        Announce a message in both text and voice channels.
        """
        # Announce in text channel
        await self._announce_text(game_timer, message)

        # Instead of playing TTS immediately, put it into a queue
        # if voice_client is connected and ready.
        if game_timer.voice_client and game_timer.voice_client.is_connected():
            # Put the message into the queue for sequential playback
            await self.queue.put((game_timer, message))
            # Start the consumer if not already running
            if not self._consumer_running:
                self._consumer_running = True
                self.consumer_task = asyncio.create_task(self._message_consumer())
        else:
            logger.warning("Voice client is not connected; cannot announce message.")

    async def _announce_text(self, game_timer, message):
        """Announce a message in the text channel."""
        if game_timer.channel:
            try:
                embed = discord.Embed(description=message, color=0x00ff00)
                await game_timer.channel.send(embed=embed)
                logger.info(f"Sent embed message to text channel: {message}")
            except Exception as e:
                logger.error(f"Error sending embed message to text channel: {e}", exc_info=True)
        else:
            logger.warning("Cannot send message; text channel is not set.")

    async def _message_consumer(self):
        """Continuously consume messages from the queue and play them sequentially."""
        try:
            while True:
                game_timer, msg = await self.queue.get()
                if game_timer.voice_client and game_timer.voice_client.is_connected():
                    try:
                        await self.tts_manager.play_tts(game_timer.voice_client, msg)
                    except Exception as e:
                        logger.error(f"Error during voice announcement: {e}", exc_info=True)
                # Mark the task as done
                self.queue.task_done()
        except asyncio.CancelledError:
            logger.info("Message consumer task cancelled")
        finally:
            self._consumer_running = False
