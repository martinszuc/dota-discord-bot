import asyncio
import os
import random

import discord

from src.communication.announcement import Announcement
from src.event_definitions import mindful_messages, mindful_pre_messages
from src.timers.base import BaseTimer
from src.utils.config import logger, MINDFUL_AUDIO_DIR


class MindfulTimer(BaseTimer):
    """
    Manages periodic mindful message announcements with text and optional audio in Discord guilds.

    This timer sends random mindful messages at random intervals and may include audio messages
    based on a specified probability.
    """

    def __init__(
        self,
        game_timer,
        min_interval: int = 600,
        max_interval: int = 900,
        audio_chance: float = 0.07
    ):
        """
        Initialize the MindfulTimer with configurable intervals and audio probability.

        Args:
            game_timer: An instance containing game state and timer-related information.
            min_interval (int, optional): Minimum interval in seconds between messages. Defaults to 600.
            max_interval (int, optional): Maximum interval in seconds between messages. Defaults to 900.
            audio_chance (float, optional): Probability (0 to 1) of sending an audio message. Defaults to 0.07.
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.audio_chance = audio_chance
        self.audio_files = self._load_audio_files()
        logger.debug(
            f"MindfulTimer initialized for guild ID {self.game_timer.guild_id} with intervals "
            f"{self.min_interval}-{self.max_interval}s and audio chance {self.audio_chance}."
        )

    def _load_audio_files(self) -> list:
        """
        Load available .mp3 files from the designated audio directory.

        Returns:
            list: A list of file paths to available audio files.
        """
        if not os.path.isdir(MINDFUL_AUDIO_DIR):
            logger.warning(f"Audio directory '{MINDFUL_AUDIO_DIR}' not found.")
            return []
        audio_files = [
            os.path.join(MINDFUL_AUDIO_DIR, f)
            for f in os.listdir(MINDFUL_AUDIO_DIR)
            if f.endswith('.mp3')
        ]
        logger.info(f"Loaded {len(audio_files)} audio files for mindful messages.")
        return audio_files

    async def _play_audio_with_tts_intro(self, channel: any) -> None:
        """
        Play a TTS message followed by an audio file in the voice channel.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        if not self.audio_files or not self.game_timer.voice_client or not self.game_timer.voice_client.is_connected():
            logger.warning("Unable to play audio. Ensure audio files are available and the bot is connected to a voice channel.")
            return

        # Select and announce a pre-message via TTS
        message = random.choice(mindful_pre_messages)["message"]
        await self.announcement.announce(self.game_timer, message)
        logger.info(f"Sent mindful TTS message in guild ID {self.game_timer.guild_id}: '{message}'")

        # Short delay before playing audio
        await self.sleep_with_pause(2)

        # Play a randomly selected audio file
        audio_file = random.choice(self.audio_files)
        audio_source = discord.FFmpegPCMAudio(audio_file)
        self.game_timer.voice_client.play(audio_source)
        logger.info(f"Playing mindful audio in guild ID {self.game_timer.guild_id}: {audio_file}")

        # Wait for audio to finish playing, checking for pause
        while self.game_timer.voice_client.is_playing():
            await self.sleep_with_pause(0.1)

    async def _run_timer(self, channel: any) -> None:
        """
        Send random mindful messages or audio at random intervals while enabled.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        logger.info(f"Starting MindfulTimer for guild ID {self.game_timer.guild_id}.")
        try:
            # Check if mindful messages are enabled; stop if disabled
            if not self.game_timer.events_manager.mindful_messages_enabled(self.game_timer.guild_id):
                logger.info(f"Mindful messages are disabled for guild ID {self.game_timer.guild_id}. Stopping MindfulTimer.")
                return  # Exit if messages are disabled

            # Initial delay before the first message
            initial_delay = random.randint(self.min_interval, self.max_interval)
            logger.debug(f"MindfulTimer initial delay: {initial_delay} seconds.")
            await self.sleep_with_pause(initial_delay)

            while self.is_running:
                # Decide whether to send an audio message based on probability
                if random.random() < self.audio_chance and self.audio_files:
                    await self._play_audio_with_tts_intro(channel)
                else:
                    # Send a random text mindful message
                    message = random.choice(mindful_messages)["message"]
                    await self.announcement.announce(self.game_timer, message)
                    logger.info(f"Sent mindful text message in guild ID {self.game_timer.guild_id}: '{message}'")

                # Set a random interval for the next message
                next_interval = random.randint(self.min_interval, self.max_interval)
                logger.debug(f"MindfulTimer waiting for {next_interval} seconds until the next message.")
                await self.sleep_with_pause(next_interval)

        except asyncio.CancelledError:
            logger.info(f"MindfulTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"MindfulTimer concluded for guild ID {self.game_timer.guild_id}.")
