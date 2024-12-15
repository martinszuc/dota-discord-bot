# src/timer.py

import asyncio

from discord.ext import tasks

from src.communication.announcement import Announcement
from src.managers.event_manager import EventsManager
from src.timers.glyph import GlyphTimer
from src.timers.mindful import MindfulTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer
from src.utils.config import logger
from src.utils.utils import parse_initial_countdown  # <--- import the new function


class GameTimer:
    """Class to manage the game timer and events."""

    def __init__(self, guild_id, mode='regular'):
        self.guild_id = guild_id
        self.mode = mode
        self.time_elapsed = 0
        self.channel = None
        self.paused = False
        self.pause_event = asyncio.Event()
        self.announcement_manager = Announcement()
        self.events_manager = EventsManager()

        # Instantiate child timers (but do NOT auto-start them, except mindful)
        self.roshan_timer = RoshanTimer(self)
        self.glyph_timer = GlyphTimer(self)
        self.tormentor_timer = TormentorTimer(self)
        self.mindful_timer = MindfulTimer(self)

        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel, countdown):
        """Start the game timer with either a countdown or already elapsed time."""
        self.channel = channel
        self.paused = False
        self.pause_event.set()

        self.time_elapsed = parse_initial_countdown(countdown)
        logger.info(f"Game timer parsed countdown '{countdown}' -> time_elapsed={self.time_elapsed} (seconds).")

        # Load event definitions for the guild and mode
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)
        logger.debug(f"Loaded static/periodic events for guild ID {self.guild_id} in mode '{self.mode}'.")

        # Start the main timer loop
        if not self.timer_task.is_running():
            self.timer_task.start()
            logger.info("GameTimer main loop started.")
        else:
            logger.debug("GameTimer main loop is already running, skipping restart.")

        # Start only the mindful timer automatically
        await self.mindful_timer.start(channel)
        logger.debug("MindfulTimer started automatically upon game start.")

    async def stop(self):
        """Stop the game timer and all child timers."""
        logger.info(f"Stopping GameTimer for guild ID {self.guild_id}.")
        self.timer_task.cancel()
        self.paused = False
        await self._stop_all_child_timers()
        logger.info(f"GameTimer and all child timers stopped for guild ID {self.guild_id}.")

    async def pause(self):
        """Pause the game timer and all child timers."""
        logger.info(f"Pausing GameTimer for guild ID {self.guild_id}.")
        self.paused = True
        self.pause_event.clear()
        await self._pause_all_child_timers()
        logger.info(f"GameTimer and all child timers paused for guild ID {self.guild_id}.")

    async def unpause(self):
        """Unpause the game timer and all child timers."""
        logger.info(f"Unpausing GameTimer for guild ID {self.guild_id}.")
        self.paused = False
        self.pause_event.set()
        await self._resume_all_child_timers()
        logger.info(f"GameTimer and all child timers resumed for guild ID {self.guild_id}.")

    @tasks.loop(seconds=1)
    async def timer_task(self):
        """Main timer loop checks events every second."""
        try:
            if self.paused:
                await self.pause_event.wait()

            self.time_elapsed += 1  # Advance the timer by 1 second
            logger.debug(f"Time elapsed: {self.time_elapsed} seconds (guild_id={self.guild_id})")

            # Check both static and periodic events
            await self._check_static_events()
            await self._check_periodic_events()

        except asyncio.CancelledError:
            logger.info(f"GameTimer loop cancelled for guild ID {self.guild_id}.")
        except Exception as e:
            logger.error(f"Unexpected error in GameTimer loop for guild ID {self.guild_id}: {e}", exc_info=True)

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in self.static_events.items():
            if self.time_elapsed == event["time"]:
                message = event['message']
                logger.info(f"Triggering static event ID {event_id} for guild ID {self.guild_id}: '{message}' at {self.time_elapsed} seconds.")
                await self.announcement_manager.announce(self, message)
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in self.periodic_events.items():
            if event["start_time"] <= self.time_elapsed <= event["end_time"]:
                if (self.time_elapsed - event["start_time"]) % event["interval"] == 0:
                    message = event['message']
                    logger.info(f"Triggering periodic event ID {event_id} for guild ID {self.guild_id}: '{message}' at {self.time_elapsed} seconds.")
                    await self.announcement_manager.announce(self, message)
                    logger.info(
                        f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")

    async def _stop_all_child_timers(self):
        """Stop roshan, glyph, tormentor, mindful timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running:
                await timer.stop()

    async def _pause_all_child_timers(self):
        """Pause roshan, glyph, tormentor, mindful timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and not timer.is_paused:
                await timer.pause()

    async def _resume_all_child_timers(self):
        """Resume roshan, glyph, tormentor, mindful timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and timer.is_paused:
                await timer.resume()

    def is_running(self):
        return self.timer_task.is_running()

    def is_paused(self):
        return self.paused
