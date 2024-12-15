import asyncio
import hashlib
import os
import re

import discord
import edge_tts

from src.utils.config import logger, TTS_CACHE_DIR


class TTSManager:
    """
    Manages Text-to-Speech (TTS) generation, caching, and playback in Discord voice channels.

    This class handles the creation and caching of TTS audio files and facilitates their playback
    in connected voice channels with volume control.
    """

    def __init__(self, voice: str = "en-GB-RyanNeural", rate: str = "0%", volume: float = 0.5):
        """
        Initialize the TTSManager with default voice settings.

        Args:
            voice (str, optional): The voice model to use for TTS. Defaults to "en-GB-RyanNeural".
            rate (str, optional): The speech rate for TTS. Defaults to "0%".
            volume (float, optional): The playback volume (0.0 to 1.0). Defaults to 0.5.
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        os.makedirs(TTS_CACHE_DIR, exist_ok=True)
        logger.debug(f"TTSManager initialized with voice={self.voice}, rate={self.rate}, volume={self.volume}.")

    async def set_voice(self, new_voice: str) -> None:
        """
        Set a new voice model for TTS.

        Args:
            new_voice (str): The identifier for the new voice model.
        """
        self.voice = new_voice
        logger.info(f"TTS voice set to {self.voice}")

    async def get_tts_audio(self, message: str) -> str:
        """
        Generate or retrieve a cached TTS audio file for a given message.

        Args:
            message (str): The text message to convert to speech.

        Returns:
            str: The file path to the TTS audio file, or None if generation failed.
        """
        # Clean the message to ensure it's safe for TTS
        clean_message = self._clean_message(message)
        if not clean_message:
            logger.warning("Cleaned message is empty. Skipping TTS generation.")
            return None

        # Generate a unique filename based on the message content
        filename = os.path.join(TTS_CACHE_DIR, f"{hashlib.md5(clean_message.encode()).hexdigest()}.mp3")

        if os.path.exists(filename):
            logger.info(f"Using cached TTS audio for message: '{clean_message}'")
        else:
            logger.info(f"Generating TTS audio for new message: '{clean_message}'")
            try:
                communicate = edge_tts.Communicate(text=clean_message, voice=self.voice)
                await communicate.save(filename)
                logger.info(f"Saved TTS audio to {filename}")
            except Exception as e:
                logger.error(f"Error generating TTS audio: {e}", exc_info=True)
                return None

        return filename

    def _clean_message(self, message: str) -> str:
        """
        Clean the input message by removing unwanted characters and extra spaces.

        Args:
            message (str): The original message.

        Returns:
            str: The cleaned message.
        """
        # Remove non-alphanumeric characters except spaces
        clean_message = re.sub(r'[^\w\s]', '', message)
        # Replace multiple spaces with a single space and strip leading/trailing spaces
        clean_message = re.sub(r'\s+', ' ', clean_message).strip()
        logger.debug(f"Cleaned message: '{clean_message}'")
        return clean_message

    async def play_tts(self, voice_client: discord.VoiceClient, message: str) -> None:
        """
        Play TTS audio in the specified Discord voice channel with volume control.

        Args:
            voice_client (discord.VoiceClient): The voice client connected to a voice channel.
            message (str): The text message to convert to speech.
        """
        audio_file = await self.get_tts_audio(message)
        if audio_file and voice_client and voice_client.is_connected():
            audio_source = discord.FFmpegPCMAudio(audio_file)
            # Apply volume control
            volume_controlled_audio = discord.PCMVolumeTransformer(audio_source, volume=self.volume)

            if not voice_client.is_playing():
                voice_client.play(volume_controlled_audio, after=lambda e: logger.info("TTS playback complete."))
                logger.info(f"Started playing audio in voice channel for message: '{message}' with volume={self.volume}")
            else:
                logger.warning("Voice client is already playing audio.")
                return

            # Wait until audio finishes playing
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
        else:
            logger.warning("Voice client is not connected or TTS audio could not be generated.")

    async def set_volume(self, new_volume: float) -> None:
        """
        Set a new playback volume for TTS audio.

        Args:
            new_volume (float): The desired volume level (0.0 to 1.0).

        Raises:
            ValueError: If the volume is outside the valid range.
        """
        if 0.0 <= new_volume <= 1.0:
            self.volume = new_volume
            logger.info(f"Volume set to {self.volume}")
        else:
            logger.warning("Invalid volume level. Volume must be between 0.0 and 1.0.")
            raise ValueError("Volume must be between 0.0 and 1.0.")
