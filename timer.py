import asyncio
import logging
import re
import os
import tempfile
import discord
from discord.ext import tasks
import edge_tts
from utils import parse_time
from events import STATIC_EVENTS, PERIODIC_EVENTS

class GameTimer:
    """Class to manage the game timer and events."""

    def __init__(self):
        self.time_elapsed = 0
        self.channel = None
        self.usernames = []  # List of discord.Member objects
        self.custom_events = {}
        self.next_event_id = max(list(STATIC_EVENTS.keys()) + list(PERIODIC_EVENTS.keys()), default=0) + 1

        # Initialize loop tasks
        self.timer_task = self._timer_task
        self.auto_stop_task = self._auto_stop_task
        self.mention_users = False
        self.paused = False
        self.pause_condition = asyncio.Condition()
        self.voice_client = None  # Discord voice client

    async def start(self, channel, countdown, usernames, mention_users=False):
        """Start the game timer."""
        self.channel = channel
        self.time_elapsed = -countdown
        self.usernames = usernames  # These are discord.Member objects
        self.mention_users = mention_users
        self.paused = False
        logging.info(f"Game timer started with countdown={countdown} seconds and usernames={usernames}")

        if self.timer_task.is_running():
            self.timer_task.cancel()
            logging.info("Existing timer task canceled before starting a new one.")
        self.timer_task.start()

        if self.auto_stop_task.is_running():
            self.auto_stop_task.cancel()
            logging.info("Existing auto-stop task canceled before starting a new one.")
        self.auto_stop_task.start()

    async def stop(self):
        """Stop the game timer."""
        if self.timer_task.is_running():
            self.timer_task.cancel()
            logging.info("Game timer task canceled.")
        if self.auto_stop_task.is_running():
            self.auto_stop_task.cancel()
            logging.info("Auto-stop task canceled.")
        self.time_elapsed = 0
        self.custom_events.clear()
        self.paused = False
        logging.info("Game timer stopped and all custom events cleared.")
        if self.channel:
            await self.channel.send("Game timer has been stopped and all events have been cleared.")
            self.channel = None
        else:
            logging.warning("Cannot send stop message; channel is not set.")
        # Disconnect voice client if connected
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None

    async def pause(self):
        """Pause the game timer."""
        self.paused = True
        logging.info("Game timer paused.")

    async def unpause(self):
        """Unpause the game timer."""
        self.paused = False
        logging.info("Game timer resumed.")
        async with self.pause_condition:
            self.pause_condition.notify_all()

    def is_running(self):
        """Check if the timer is running."""
        return self.timer_task.is_running()

    def add_event(self, start_time, message, target_group):
        """Add a static event with a unique ID."""
        event_time = parse_time(start_time)
        # Check for duplicate event times in STATIC_EVENTS
        for event in STATIC_EVENTS.values():
            if event["time"] == start_time and event["message"] == message:
                raise ValueError(f"❌ An event with message '{message}' at time '{start_time}' already exists.")
        # Assign a unique ID
        event_id = self.next_event_id
        STATIC_EVENTS[event_id] = {"time": start_time, "message": message, "target_groups": [target_group]}
        self.next_event_id += 1
        logging.info(
            f"Static event added: ID={event_id}, time={start_time}, message='{message}', target_group='{target_group}'")
        return event_id

    def add_custom_event(self, start_time, interval, end_time, message, target_groups):
        """Add a custom periodic event with a unique ID."""
        start_seconds = parse_time(start_time)
        interval_seconds = parse_time(interval)
        end_seconds = parse_time(end_time)

        if interval_seconds <= 0:
            raise ValueError("❌ Interval must be greater than 0 seconds.")
        if end_seconds <= start_seconds:
            raise ValueError("❌ End time must be after start time.")

        event_id = self.next_event_id
        self.custom_events[event_id] = {
            "start_time": start_seconds,
            "interval": interval_seconds,
            "end_time": end_seconds,
            "message": message,
            "target_groups": target_groups
        }
        self.next_event_id += 1
        logging.info(
            f"Custom periodic event added: ID={event_id}, start_time={start_time}, interval={interval}, end_time={end_time}, message='{message}', target_groups={target_groups}")
        return event_id

    def remove_custom_event(self, event_id):
        """Remove a custom periodic event by its unique ID."""
        if event_id in self.custom_events:
            del self.custom_events[event_id]
            logging.info(f"Custom event ID {event_id} removed.")
            return True
        else:
            logging.warning(f"Attempted to remove non-existent custom event ID {event_id}.")
            return False

    def get_custom_events(self):
        """Get all custom periodic events."""
        return self.custom_events

    def is_paused(self):
        """Check if the timer is paused."""
        return self.paused

    @tasks.loop(seconds=1)
    async def _timer_task(self):
        """Main timer loop that checks events every second."""
        while True:
            if self.paused:
                logging.debug("Game timer is paused.")
                async with self.pause_condition:
                    await self.pause_condition.wait()
            self.time_elapsed += 1
            logging.debug(f"Time elapsed: {self.time_elapsed} seconds")
            try:
                await self._check_static_events()
                await self._check_periodic_events()
                await self._check_custom_events()
            except Exception as e:
                logging.error(f"Error in _timer_task: {e}", exc_info=True)
            await asyncio.sleep(1)

    @tasks.loop(seconds=1)
    async def _auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:  # 1.5 hours in seconds
            await self.stop()
            logging.info("Game timer automatically stopped after 1.5 hours.")
            if self.channel:
                await self.channel.send("Game timer automatically stopped after 1.5 hours.")

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in STATIC_EVENTS.items():
            event_time = parse_time(event["time"])
            if self.time_elapsed == event_time:
                message = event['message']
                await self.announce_message(message)
                logging.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in PERIODIC_EVENTS.items():
            start_seconds = parse_time(event["start_time"])
            interval_seconds = parse_time(event["interval"])
            end_seconds = parse_time(event["end_time"])
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    message = event['message']
                    await self.announce_message(message)
                    logging.info(f"Predefined periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}'")

    async def _check_custom_events(self):
        """Check and trigger custom periodic events."""
        for event_id, event in self.custom_events.items():
            start_seconds = event["start_time"]
            interval_seconds = event["interval"]
            end_seconds = event["end_time"]
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    message = event['message']
                    await self.announce_message(message)
                    logging.info(f"Custom periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}'")

    async def announce_message(self, message):
        """Announce a message in the voice channel."""
        # Send message in text channel
        if self.channel:
            await self.channel.send(message)
            logging.info(f"Sent message to text channel: {message}")
        else:
            logging.warning("Cannot send message; text channel is not set.")

        # Announce message in voice channel
        if self.voice_client and self.voice_client.is_connected():
            try:
                # Remove unwanted symbols from the message
                clean_message = re.sub(r'[^\w\s]', '', message)
                clean_message = re.sub(r'\s+', ' ', clean_message).strip()
                logging.info(f"Cleaned message for TTS: '{clean_message}'")

                if not clean_message:
                    logging.warning("Cleaned message is empty. Skipping TTS announcement.")
                    return

                # Select the desired voice
                voice = "en-US-AmberNeural"  # Change this to your preferred voice
                logging.info(f"Using voice: {voice}")

                # Generate speech audio from message using edge_tts
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                communicate = edge_tts.Communicate(text=clean_message, voice=voice)
                logging.info(f"Generating TTS audio for message: '{clean_message}'")
                await communicate.save(output_file.name)
                logging.info(f"Saved TTS audio to {output_file.name}")

                # Play the audio in the voice channel
                audio_source = discord.FFmpegPCMAudio(output_file.name)
                if not self.voice_client.is_playing():
                    self.voice_client.play(audio_source)
                    logging.info("Started playing audio in voice channel.")
                else:
                    logging.warning("Voice client is already playing audio.")

                # Wait until playback is finished
                while self.voice_client.is_playing():
                    await asyncio.sleep(0.1)

                # Clean up temporary audio file
                output_file.close()
                os.unlink(output_file.name)
                logging.info("Finished playing audio and cleaned up temporary file.")
            except Exception as e:
                logging.error(f"Error during voice announcement: {e}", exc_info=True)
        else:
            logging.warning("Voice client is not connected; cannot announce message.")

    async def start_glyph_timer(self, channel):
        """Start a 5-minute timer for the enemy's glyph cooldown."""
        glyph_cooldown = 5 * 60  # 5 minutes in seconds
        await asyncio.sleep(glyph_cooldown - 30)  # Notify 30 seconds before cooldown ends
        message = "Enemy glyph available in 30 seconds!"
        await channel.send(message)
        await self.announce_message(message)
        await asyncio.sleep(30)
        message = "Enemy glyph cooldown has ended!"
        await channel.send(message)
        await self.announce_message(message)
        logging.info("Enemy glyph cooldown ended.")
