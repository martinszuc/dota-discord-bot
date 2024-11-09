# timer.py

import asyncio

from discord.ext import tasks

from communication import Announcement
from src.utils.config import logger
from src.managers.event_manager import EventsManager
from .timers.glyph import GlyphTimer
from .timers.roshan import RoshanTimer

# Initialize Announcement once
announcement_manager = Announcement()

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
        self.roshan_timer = RoshanTimer(self)  # Integrate RoshanTimer here
        self.glyph_timer = GlyphTimer(self)    # Integrate GlyphTimer here

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
        self.static_events = events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = events_manager.get_periodic_events(self.guild_id, self.mode)
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

        # Announce stop message
        await announcement_manager.announce(self, "Good game! Well played everyone!")

        # Disconnect voice client if connected
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            logger.info("Voice client disconnected.")

        # Cancel Roshan timer if active
        if self.roshan_timer.is_active:
            await self.roshan_timer.cancel()
            logger.info("Roshan timer cancelled.")

        # Cancel Glyph timer if active
        if self.glyph_timer.is_active:
            await self.glyph_timer.cancel()
            logger.info("Glyph timer cancelled.")

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
            await announcement_manager.announce(self, "Game timer automatically stopped after 1.5 hours.")

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in self.static_events.items():
            if self.time_elapsed == event["time"]:
                message = event['message']
                await announcement_manager.announce(self, message)
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in self.periodic_events.items():
            if event["start_time"] <= self.time_elapsed <= event["end_time"]:
                if (self.time_elapsed - event["start_time"]) % event["interval"] == 0:
                    message = event['message']
                    await announcement_manager.announce(self, message)
                    logger.info(f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")
