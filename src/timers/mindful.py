# src/timers/mindful.py

import asyncio
import random
import os
import discord
from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger, MINDFUL_AUDIO_DIR
from src.event_definitions import mindful_messages, mindful_pre_messages


class MindfulTimer(BaseTimer):
    """Manages periodic mindful message announcements, with text and optional audio selection."""

    def __init__(self, game_timer, min_interval=600, max_interval=900, audio_chance=0.10):
        """
        Initialize MindfulTimer with text and optional audio functionality.

        :param game_timer: Reference to the main game timer
        :param min_interval: Minimum interval (seconds) between messages
        :param max_interval: Maximum interval (seconds) between messages
        :param audio_chance: Probability (0 to 1) of sending an audio message
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.audio_chance = audio_chance
        self.audio_files = self._load_audio_files()
        logger.debug(f"MindfulTimer initialized for guild ID {self.game_timer.guild_id} with intervals {self.min_interval}-{self.max_interval}s and audio chance {self.audio_chance}.")

    def _load_audio_files(self):
        """Load available .mp3 files from the audio directory."""
        if not os.path.isdir(MINDFUL_AUDIO_DIR):
            logger.warning(f"Audio directory '{MINDFUL_AUDIO_DIR}' not found.")
            return []
        audio_files = [os.path.join(MINDFUL_AUDIO_DIR, f) for f in os.listdir(MINDFUL_AUDIO_DIR) if f.endswith('.mp3')]
        logger.info(f"Loaded {len(audio_files)} audio files for mindful messages.")
        return audio_files

    async def _play_audio_with_tts_intro(self, channel):
        """Play a TTS message followed by an audio file in the voice channel."""
        if not self.audio_files or not self.game_timer.voice_client or not self.game_timer.voice_client.is_connected():
            logger.warning("Unable to play audio. Ensure audio files are available and the bot is connected to a voice channel.")
            return

        # Send a TTS message before playing audio
        message = random.choice(mindful_pre_messages)["message"]
        await self.announcement.announce(self.game_timer, message)
        logger.info(f"Sent mindful TTS message in guild ID {self.game_timer.guild_id}: '{message}'")

        # Short delay before playing audio
        await asyncio.sleep(2)

        # Play a random audio file
        audio_file = random.choice(self.audio_files)
        audio_source = discord.FFmpegPCMAudio(audio_file)
        self.game_timer.voice_client.play(audio_source)
        logger.info(f"Playing mindful audio in guild ID {self.game_timer.guild_id}: {audio_file}")

        # Wait for audio to finish playing
        while self.game_timer.voice_client.is_playing():
            await asyncio.sleep(0.1)

    async def _run_timer(self, channel):
        """Send a random mindful message or audio with TTS intro at random intervals while enabled."""
        logger.info(f"Starting MindfulTimer for guild ID {self.game_timer.guild_id}.")
        try:
            # Check if mindful messages are enabled, stop if disabled
            if not self.game_timer.events_manager.mindful_messages_enabled(self.game_timer.guild_id):
                logger.info(f"Mindful messages are disabled for guild ID {self.game_timer.guild_id}. Stopping MindfulTimer.")
                return  # Exit _run_timer if messages are disabled

            # Initial delay before the first message (10 to 15 minutes)
            initial_delay = random.randint(self.min_interval, self.max_interval)
            logger.debug(f"Initial delay set to {initial_delay} seconds.")
            await asyncio.sleep(initial_delay)

            while self.is_running:
                # Randomly choose between a text or audio message
                if random.random() < self.audio_chance and self.audio_files:
                    await self._play_audio_with_tts_intro(channel)
                else:
                    message = random.choice(mindful_messages)["message"]
                    await self.announcement.announce(self.game_timer, message)
                    logger.info(f"Sent mindful text message in guild ID {self.game_timer.guild_id}: '{message}'")

                # Set a random interval between min_interval and max_interval for the next message
                next_interval = random.randint(self.min_interval, self.max_interval)
                logger.debug(f"Waiting {next_interval} seconds until the next mindful message.")
                await asyncio.sleep(next_interval)

        except asyncio.CancelledError:
            logger.info(f"MindfulTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"MindfulTimer concluded for guild ID {self.game_timer.guild_id}.")