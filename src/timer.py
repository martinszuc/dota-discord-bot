# src/timer.py

import asyncio
from discord.ext import tasks
from src.communication.announcement import Announcement
from src.utils.config import logger
from src.managers.event_manager import EventsManager
from src.timers.glyph import GlyphTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer
from src.timers.mindful import MindfulTimer
from src.utils.utils import min_to_sec

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

        # Initialize child timers
        self.roshan_timer = RoshanTimer(self)
        self.glyph_timer = GlyphTimer(self)
        self.tormentor_timer = TormentorTimer(self)
        self.mindful_timer = MindfulTimer(self)

        # Initialize event dictionaries
        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel, countdown):
        """Start the game timer with either a countdown or elapsed time."""
        self.channel = channel
        self.paused = False
        self.pause_event.set()

        # Check if countdown is in 'mm:ss' format or integer seconds
        if isinstance(countdown, str):
            if countdown.startswith("-"):
                # Remove the negative sign, convert to seconds, and set as positive elapsed time
                self.time_elapsed = min_to_sec(countdown[1:])
                logger.debug(f"Count down string detected as negative. Set time_elapsed to {self.time_elapsed} seconds.")
            else:
                # Countdown delay if positive mm:ss format
                self.time_elapsed = -min_to_sec(countdown)
                logger.debug(f"Count down string detected as positive. Set time_elapsed to {self.time_elapsed} seconds.")
        elif isinstance(countdown, int):
            # Handle integer countdown directly
            if countdown < 0:
                # Negative countdown: set as positive elapsed time
                self.time_elapsed = abs(countdown)
                logger.debug(f"Count down integer detected as negative. Set time_elapsed to {self.time_elapsed} seconds.")
            else:
                # Positive countdown: set as negative to use as delay
                self.time_elapsed = -countdown
                logger.debug(f"Count down integer detected as positive. Set time_elapsed to {self.time_elapsed} seconds.")

        logger.info(f"Game timer started with countdown={countdown} seconds in mode='{self.mode}'.")

        # Load events for the guild and mode
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)
        logger.debug(f"Loaded static and periodic events for guild ID {self.guild_id} in mode '{self.mode}'.")

        # Start the timer task
        if not self.timer_task.is_running():
            self.timer_task.start()
            logger.info("Timer task started.")
        else:
            logger.debug("Timer task is already running.")

        # Start child timers
        await self.mindful_timer.start(channel)
        logger.debug("MindfulTimer started.")

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
        """Main timer loop that checks events every second."""
        try:
            if self.paused:
                logger.debug("GameTimer is paused. Waiting to unpause.")
                await self.pause_event.wait()

            self.time_elapsed += 1  # Advance the timer
            logger.debug(f"Time elapsed: {self.time_elapsed} seconds")

            try:
                # Check both static and periodic events
                await self._check_static_events()
                await self._check_periodic_events()
            except Exception as e:
                logger.error(f"Error in timer_loop: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.info(f"Timer loop for guild ID {self.guild_id} has been cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in timer_loop: {e}", exc_info=True)

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
        """Helper method to stop all child timers."""
        logger.debug(f"Stopping all child timers for guild ID {self.guild_id}.")
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running:
                logger.debug(f"Stopping {timer.__class__.__name__} for guild ID {self.guild_id}.")
                try:
                    await timer.stop()
                except Exception as e:
                    logger.error(f"Error stopping {timer.__class__.__name__} for guild ID {self.guild_id}: {e}", exc_info=True)

    async def _pause_all_child_timers(self):
        """Helper method to pause all child timers."""
        logger.debug(f"Pausing all child timers for guild ID {self.guild_id}.")
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and not timer.is_paused:
                logger.debug(f"Pausing {timer.__class__.__name__} for guild ID {self.guild_id}.")
                try:
                    await timer.pause()
                except Exception as e:
                    logger.error(f"Error pausing {timer.__class__.__name__} for guild ID {self.guild_id}: {e}", exc_info=True)

    async def _resume_all_child_timers(self):
        """Helper method to resume all child timers."""
        logger.debug(f"Resuming all child timers for guild ID {self.guild_id}.")
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and timer.is_paused:
                logger.debug(f"Resuming {timer.__class__.__name__} for guild ID {self.guild_id}.")
                try:
                    await timer.resume()
                except Exception as e:
                    logger.error(f"Error resuming {timer.__class__.__name__} for guild ID {self.guild_id}: {e}", exc_info=True)

    def close(self):
        """Clean up resources."""
        self.events_manager.close()
        logger.debug(f"GameTimer for guild ID {self.guild_id} closed.")

    def is_running(self):
        """Check if the game timer is running."""
        return self.timer_task.is_running()

    def is_paused(self):
        """Check if the game timer is paused."""
        return self.paused
