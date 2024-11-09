import asyncio
import hashlib
import os
import discord
import re
import edge_tts
from src.utils.config import logger, TTS_CACHE_DIR

class TTSManager:
    """A class to manage TTS generation, caching, and playback in Discord voice channels."""

    def __init__(self, voice="en-US-AriaNeural"):
        self.voice = voice

    async def get_tts_audio(self, message):
        """Generates or retrieves TTS audio for a given message."""
        # Clean the message to make it safe for TTS
        clean_message = re.sub(r'[^\w\s]', '', message)
        clean_message = re.sub(r'\s+', ' ', clean_message).strip()

        if not clean_message:
            logger.warning("Cleaned message is empty. Skipping TTS generation.")
            return None

        # Generate a unique filename based on the message
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

    async def play_tts(self, voice_client, message):
        """Plays TTS audio in the specified voice client channel."""
        audio_file = await self.get_tts_audio(message)
        if audio_file and voice_client and voice_client.is_connected():
            audio_source = discord.FFmpegPCMAudio(audio_file)
            if not voice_client.is_playing():
                voice_client.play(audio_source, after=lambda e: logger.info("TTS playback complete."))
                logger.info(f"Started playing audio in voice channel for message: '{message}'")
            else:
                logger.warning("Voice client is already playing audio.")

            # Wait until audio finishes playing
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
        else:
            logger.warning("Voice client is not connected or TTS audio could not be generated.")
