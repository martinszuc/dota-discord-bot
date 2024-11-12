# src/timers/mindful.py

import asyncio
import random
import os

import discord

from src.communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger, MINDFUL_AUDIO_DIR  # Ensure MINDFUL_AUDIO_DIR is defined in config
from src.event_definitions import mindful_messages, mindful_pre_messages


class MindfulTimer(BaseTimer):
    """Class to manage periodic mindful message announcements, with random text or audio selection."""

    def __init__(self, game_timer, min_interval=600, max_interval=900, audio_chance=0.09):
        """
        Initialize MindfulTimer with text and optional audio message functionality.

        :param game_timer: Reference to the main game timer
        :param min_interval: Minimum time interval between messages
        :param max_interval: Maximum time interval between messages
        :param audio_chance: Probability (0 to 1) of selecting an audio file instead of text for each announcement
        """
        super().__init__(game_timer)
        self.announcement = Announcement()
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.audio_chance = audio_chance
        self.audio_files = self._load_audio_files()
        logger.debug(
            f"MindfulTimer initialized for guild ID {self.game_timer.guild_id} with interval {self.min_interval}-{self.max_interval}s and audio chance {self.audio_chance}.")

    def _load_audio_files(self):
        """Load available .mp3 files from the audio directory."""
        if not os.path.isdir(MINDFUL_AUDIO_DIR):
            logger.warning(f"Audio directory '{MINDFUL_AUDIO_DIR}' not found.")
            return []
        audio_files = [os.path.join(MINDFUL_AUDIO_DIR, f) for f in os.listdir(MINDFUL_AUDIO_DIR) if f.endswith('.mp3')]
        logger.info(f"Loaded {len(audio_files)} audio files for mindful messages.")
        return audio_files

    async def _play_audio_with_tts_intro(self, channel):
        """Play a TTS message followed by a random .mp3 audio file in the voice channel."""
        if not self.audio_files:
            logger.warning("No audio files available to play.")
            return
        if not self.game_timer.voice_client or not self.game_timer.voice_client.is_connected():
            logger.warning("Voice client is not connected; cannot play audio.")
            return

        # Send a mindful TTS message
        message = random.choice(mindful_pre_messages)["message"]
        await self.announcement.announce(self.game_timer, message)
        logger.info(f"Mindful TTS message sent in guild ID {self.game_timer.guild_id}: '{message}'")

        # Short delay before playing audio
        await asyncio.sleep(2)

        # Play the audio file
        audio_file = random.choice(self.audio_files)
        audio_source = discord.FFmpegPCMAudio(audio_file)
        self.game_timer.voice_client.play(audio_source)
        logger.info(f"Playing mindful audio in guild ID {self.game_timer.guild_id}: {audio_file}")

        # Wait until audio finishes playing
        while self.game_timer.voice_client.is_playing():
            await asyncio.sleep(0.1)

    async def _run_timer(self, channel):
        """Send a random mindful message or audio with TTS intro at random intervals while enabled."""
        logger.info(f"MindfulTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            while self.is_running:
                if not self.game_timer.events_manager.mindful_messages_enabled(self.game_timer.guild_id):
                    logger.debug(
                        f"Mindful messages are disabled for guild ID {self.game_timer.guild_id}. Waiting before next check.")
                    await asyncio.sleep(self.max_interval)
                    continue

                # Decide randomly between sending a text message or a TTS with audio file
                if random.random() < self.audio_chance and self.audio_files:
                    await self._play_audio_with_tts_intro(channel)
                else:
                    message = random.choice(mindful_messages)["message"]
                    await self.announcement.announce(self.game_timer, message)
                    logger.info(f"Mindful text message sent in guild ID {self.game_timer.guild_id}: '{message}'")

                # Wait for a random interval between min_interval and max_interval before sending the next message
                random_interval = random.randint(self.min_interval, self.max_interval)
                logger.debug(f"MindfulTimer will wait for {random_interval} seconds before next message.")
                await asyncio.sleep(random_interval)

        except asyncio.CancelledError:
            logger.info(f"MindfulTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"MindfulTimer concluded for guild ID {self.game_timer.guild_id}.")
