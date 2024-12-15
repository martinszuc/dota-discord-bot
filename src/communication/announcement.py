import discord

from src.managers.tts_manager import TTSManager
from src.utils.config import logger


class Announcement:
    """A class to manage announcements in text and voice channels."""

    def __init__(self):
        self.tts_manager = TTSManager()

    async def announce(self, game_timer, message):
        """
        Announce a message in both text and voice channels.

        Parameters:
            game_timer (GameTimer): The GameTimer instance managing the current game.
            message (str): The message to announce.
        """
        # Announce in text channel
        if game_timer.channel:
            try:
                embed = discord.Embed(description=message, color=0x00ff00)
                await game_timer.channel.send(embed=embed)
                logger.info(f"Sent embed message to text channel: {message}")
            except Exception as e:
                logger.error(f"Error sending embed message to text channel: {e}", exc_info=True)
        else:
            logger.warning("Cannot send message; text channel is not set.")

        # Announce in voice channel using TTSManager
        if game_timer.voice_client and game_timer.voice_client.is_connected():
            try:
                await self.tts_manager.play_tts(game_timer.voice_client, message)
            except Exception as e:
                logger.error(f"Error during voice announcement: {e}", exc_info=True)
        else:
            logger.warning("Voice client is not connected; cannot announce message.")
