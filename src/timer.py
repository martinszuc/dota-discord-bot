# src/timer.py

import asyncio
from discord.ext import tasks
from communication.announcement import Announcement
from src.utils.config import logger
from src.managers.event_manager import EventsManager
from src.timers.glyph import GlyphTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer


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

        # Initialize event dictionaries
        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel, countdown):
        """Start the game timer."""
        self.channel = channel
        self.time_elapsed = -countdown
        self.paused = False
        self.pause_event.set()

        # Load events for the guild and mode
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)

        logger.info(f"Game timer started with countdown={countdown} seconds in mode={self.mode}.")

        # Start the timer task
        if not self.timer_task.is_running():
            self.timer_task.start()

    async def stop(self):
        """Stop the game timer and all child timers."""
        self.timer_task.cancel()
        self.paused = False
        await self._stop_all_child_timers()
        logger.info("Game timer and all child timers stopped.")

    async def pause(self):
        """Pause the game timer and all child timers."""
        self.paused = True
        self.pause_event.clear()
        await self.events_manager.pause_all_events()
        logger.info("Game timer and all child timers paused.")

    async def unpause(self):
        """Unpause the game timer and all child timers."""
        self.paused = False
        self.pause_event.set()
        await self.events_manager.resume_all_events()
        logger.info("Game timer and all child timers resumed.")

    @tasks.loop(seconds=1)
    async def timer_task(self):
        """Main timer loop that checks events every second."""
        if self.paused:
            await self.pause_event.wait()
        self.time_elapsed += 1
        logger.debug(f"Time elapsed: {self.time_elapsed} seconds")

        try:
            await self._check_static_events()
            await self._check_periodic_events()
        except Exception as e:
            logger.error(f"Error in timer_task: {e}", exc_info=True)

    @tasks.loop(seconds=1)
    async def auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:
            await self.stop()
            logger.info("Game timer automatically stopped after 1.5 hours.")

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in self.static_events.items():
            if self.time_elapsed == event["time"]:
                message = event['message']
                await self.announcement_manager.announce(self, message)
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in self.periodic_events.items():
            if event["start_time"] <= self.time_elapsed <= event["end_time"]:
                if (self.time_elapsed - event["start_time"]) % event["interval"] == 0:
                    message = event['message']
                    await self.announcement_manager.announce(self, message)
                    logger.info(f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")

    async def _stop_all_child_timers(self):
        """Helper method to stop all child timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer]:
            if timer.is_running:
                await timer.stop()

    async def _pause_all_child_timers(self):
        """Helper method to pause all child timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer]:
            if timer.is_running:
                await timer.pause()

    async def _resume_all_child_timers(self):
        """Helper method to resume all child timers."""
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer]:
            if timer.is_paused:
                await timer.resume()

    def close(self):
        """Clean up resources."""
        self.events_manager.close()

    def is_running(self):
        """Check if the game timer is running."""
        return self.timer_task.is_running()

    def is_paused(self):
        """Check if the game timer is paused."""
        return self.paused
