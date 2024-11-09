# timer.py

import asyncio
import logging
import re
import os
import tempfile
import discord
from discord.ext import tasks
import edge_tts
from utils import parse_time
from event_manager import EventsManager

logger = logging.getLogger(__name__)

class GameTimer:
    """Class to manage the game timer and events."""

    def __init__(self, guild_id, mode='regular'):
        self.guild_id = guild_id
        self.mode = mode
        self.time_elapsed = 0
        self.channel = None
        self.usernames = []
        self.custom_events = {}
        self.paused = False
        self.pause_condition = asyncio.Condition()
        self.voice_client = None

        self.timer_task = self._timer_task
        self.auto_stop_task = self._auto_stop_task
        self.mention_users = False

        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel, countdown, usernames, mention_users=False):
        """Start the game timer."""
        self.channel = channel
        self.time_elapsed = -countdown
        self.usernames = usernames
        self.mention_users = mention_users
        self.paused = False
        logger.info(f"Game timer started with countdown={countdown} seconds and usernames={usernames} in mode={self.mode}")

        # Load events from database
        events_manager = EventsManager()
        self.static_events, self.periodic_events = events_manager.get_events(self.guild_id, self.mode)
        events_manager.close()

        # Start the timer task if not already running
        if not self.timer_task.is_running():
            self.timer_task.start()
            logger.info("Timer task started.")

        # Start the auto-stop task if not already running
        if not self.auto_stop_task.is_running():
            self.auto_stop_task.start()
            logger.info("Auto-stop task started.")

    async def stop(self):
        """Stop the game timer."""
        if self.timer_task.is_running():
            self.timer_task.cancel()
            logger.info("Timer task canceled.")
        if self.auto_stop_task.is_running():
            self.auto_stop_task.cancel()
            logger.info("Auto-stop task canceled.")

        self.time_elapsed = 0
        self.paused = False
        logger.info("Game timer stopped.")

        if self.channel:
            await self.channel.send("Game timer has been stopped and all events have been cleared.", tts=True)
            self.channel = None
        else:
            logger.warning("Cannot send stop message; channel is not set.")

        # Disconnect voice client if connected
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            logger.info("Voice client disconnected.")

    async def pause(self):
        """Pause the game timer."""
        self.paused = True
        logger.info("Game timer paused.")

    async def unpause(self):
        """Unpause the game timer."""
        self.paused = False
        logger.info("Game timer resumed.")
        async with self.pause_condition:
            self.pause_condition.notify_all()

    def is_running(self):
        """Check if the timer is running."""
        return self.timer_task.is_running()

    def is_paused(self):
        """Check if the timer is paused."""
        return self.paused

    @tasks.loop(seconds=1)
    async def _timer_task(self):
        """Main timer loop that checks events every second."""
        if self.paused:
            logger.debug("Game timer is paused.")
            async with self.pause_condition:
                await self.pause_condition.wait()

        self.time_elapsed += 1
        logger.debug(f"Time elapsed: {self.time_elapsed} seconds")
        try:
            await self._check_static_events()
            await self._check_periodic_events()
        except Exception as e:
            logger.error(f"Error in _timer_task: {e}", exc_info=True)

    @tasks.loop(seconds=1)
    async def _auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:
            await self.stop()
            logger.info("Game timer automatically stopped after 1.5 hours.")
            if self.channel:
                await self.channel.send("Game timer automatically stopped after 1.5 hours.", tts=True)

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in self.static_events.items():
            event_time = parse_time(event["time"])
            if self.time_elapsed == event_time:
                message = event['message']
                await self.announce_message(message)
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in self.periodic_events.items():
            start_seconds = parse_time(event["start_time"])
            interval_seconds = parse_time(event["interval"])
            end_seconds = parse_time(event["end_time"])
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    message = event['message']
                    await self.announce_message(message)
                    logger.info(f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")

    async def announce_message(self, message):
        """Announce a message in the voice channel."""
        # Send message in text channel using embeds
        if self.channel:
            embed = discord.Embed(description=message, color=0x00ff00)
            await self.channel.send(embed=embed, tts=True)
            logger.info(f"Sent embed message to text channel: {message}")
        else:
            logger.warning("Cannot send message; text channel is not set.")

        # Announce message in voice channel
        if self.voice_client and self.voice_client.is_connected():
            try:
                clean_message = re.sub(r'[^\w\s]', '', message)
                clean_message = re.sub(r'\s+', ' ', clean_message).strip()
                logger.info(f"Cleaned message for TTS: '{clean_message}'")

                if not clean_message:
                    logger.warning("Cleaned message is empty. Skipping TTS announcement.")
                    return

                voice = "en-US-AriaNeural"
                logger.info(f"Using voice: {voice}")

                output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                communicate = edge_tts.Communicate(text=clean_message, voice=voice)
                logger.info(f"Generating TTS audio for message: '{clean_message}'")
                await communicate.save(output_file.name)
                logger.info(f"Saved TTS audio to {output_file.name}")

                audio_source = discord.FFmpegPCMAudio(output_file.name)
                if not self.voice_client.is_playing():
                    self.voice_client.play(audio_source)
                    logger.info("Started playing audio in voice channel.")
                else:
                    logger.warning("Voice client is already playing audio.")

                while self.voice_client.is_playing():
                    await asyncio.sleep(0.1)

                output_file.close()
                os.unlink(output_file.name)
                logger.info("Finished playing audio and cleaned up temporary file.")
            except Exception as e:
                logger.error(f"Error during voice announcement: {e}", exc_info=True)
        else:
            logger.warning("Voice client is not connected; cannot announce message.")

    async def start_glyph_timer(self, channel):
        """Start a 5-minute timer for the enemy's glyph cooldown."""
        glyph_cooldown = 5 * 60
        await asyncio.sleep(glyph_cooldown - 30)
        message = "Enemy glyph available in 30 seconds!"
        await channel.send(message, tts=True)
        await self.announce_message(message)
        await asyncio.sleep(30)
        message = "Enemy glyph cooldown has ended!"
        await channel.send(message, tts=True)
        await self.announce_message(message)
        logger.info("Enemy glyph cooldown ended.")
