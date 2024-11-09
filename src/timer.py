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
        self.usernames = []
        self.custom_events = {}
        self.paused = False
        self.pause_condition = asyncio.Condition()
        self.voice_client = None

        self.announcement_manager = Announcement()
        self.events_manager = EventsManager()

        # Initialize child timers
        self.roshan_timer = RoshanTimer(self)
        self.glyph_timer = GlyphTimer(self)
        self.tormentor_timer = TormentorTimer(self)

    async def start(self, channel, countdown, usernames, mention_users=False):
        """Start the game timer."""
        self.channel = channel
        self.time_elapsed = -countdown
        self.usernames = usernames
        self.mention_users = mention_users
        self.paused = False
        logger.info(f"Game timer started with countdown={countdown} seconds and usernames={usernames} in mode={self.mode}")

        # Load events from database
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)

        # Start child timers if needed
        # (They can be started via bot commands)

        # Start the timer task
        self.timer_task.start()

    async def stop(self):
        """Stop the game timer and all child timers."""
        self.timer_task.cancel()
        self.auto_stop_task.cancel()

        self.time_elapsed = 0
        self.paused = False
        logger.info("Game timer stopped.")

        # Stop all child timers
        await asyncio.gather(
            self.roshan_timer.stop(),
            self.glyph_timer.stop(),
            self.tormentor_timer.stop(),
            return_exceptions=True
        )

        # Disconnect voice client if connected
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            logger.info("Voice client disconnected.")

    async def pause(self):
        """Pause the game timer and all child timers."""
        self.paused = True
        logger.info("Game timer paused.")

        # Pause child timers
        await asyncio.gather(
            self.roshan_timer.pause(),
            self.glyph_timer.pause(),
            self.tormentor_timer.pause(),
            return_exceptions=True
        )

    async def unpause(self):
        """Unpause the game timer and all child timers."""
        self.paused = False
        logger.info("Game timer resumed.")

        # Unpause child timers
        await asyncio.gather(
            self.roshan_timer.resume(),
            self.glyph_timer.resume(),
            self.tormentor_timer.resume(),
            return_exceptions=True
        )

    def is_running(self):
        """Check if the game timer is running."""
        return self.timer_task.is_running()

    def is_paused(self):
        """Check if the game timer is paused."""
        return self.paused

    @tasks.loop(seconds=1)
    async def timer_task(self):
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

    def close(self):
        """Clean up resources."""
        self.events_manager.close()
