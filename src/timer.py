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
        self.voice_client = None
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.announcement_manager = Announcement()
        self.events_manager = EventsManager()

        # Initialize child timers
        self.roshan_timer = RoshanTimer(self)
        self.glyph_timer = GlyphTimer(self)
        self.tormentor_timer = TormentorTimer(self)
        self.mindful_timer = MindfulTimer(self)

        self.running = False

        # Initialize event dictionaries
        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel, countdown):
        """Start the game timer with either a countdown or elapsed time."""
        self.channel = channel
        self.paused = False
        self.pause_event.set()

        # Parse countdown
        if isinstance(countdown, str):
            if countdown.startswith("-"):
                self.time_elapsed = min_to_sec(countdown[1:])
                logger.debug(f"Countdown string detected as negative. Set time_elapsed to {self.time_elapsed} seconds.")
            else:
                self.time_elapsed = -min_to_sec(countdown)
                logger.debug(f"Countdown string detected as positive. Set time_elapsed to {self.time_elapsed} seconds.")
        elif isinstance(countdown, int):
            self.time_elapsed = -countdown if countdown > 0 else abs(countdown)
            logger.debug(f"Countdown integer detected. Set time_elapsed to {self.time_elapsed} seconds.")

        logger.info(f"Game timer started with countdown={countdown} mode='{self.mode}' for guild {self.guild_id}.")

        # Load events
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)
        logger.debug(f"Loaded static and periodic events for guild ID {self.guild_id} in mode '{self.mode}'.")

        # Start the master loop
        if not self.timer_task.is_running():
            self.timer_task.start()
            self.running = True
            logger.info("Timer task started.")

        # Start child timers
        self.roshan_timer.setup()
        self.glyph_timer.setup()
        self.tormentor_timer.setup()
        self.mindful_timer.enable()

    async def stop(self):
        """Stop the game timer and all child timers."""
        if not self.running:
            logger.warning("Stop called but the timer is not running.")
            return

        logger.info(f"Stopping GameTimer for guild {self.guild_id}.")
        self.running = False
        self.paused = False
        self.pause_event.set()

        # Stop the loop
        if self.timer_task.is_running():
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass

        # Stop child timers
        self.roshan_timer.reset()
        self.glyph_timer.reset()
        self.tormentor_timer.reset()
        self.mindful_timer.disable()

        logger.info(f"GameTimer and all child timers stopped for guild {self.guild_id}.")

    async def pause(self):
        if not self.running:
            await self.channel.send("No active game timer found.")
            return

        self.paused = True
        self.pause_event.clear()
        logger.info(f"GameTimer paused for guild {self.guild_id}.")
        await self.channel.send("Game timer paused.")

    async def unpause(self):
        if not self.running:
            await self.channel.send("No active game timer found.")
            return

        self.paused = False
        self.pause_event.set()
        logger.info(f"GameTimer unpaused for guild {self.guild_id}.")
        await self.channel.send("Game timer resumed.")

    @tasks.loop(seconds=1)
    async def timer_task(self):
        """Main timer loop."""
        try:
            if not self.running:
                return

            if self.paused:
                # Wait until unpaused
                await self.pause_event.wait()

            self.time_elapsed += 1
            logger.debug(f"Time elapsed: {self.time_elapsed} seconds")

            await self._check_static_events()
            await self._check_periodic_events()

            # Check and trigger child timer events
            await self.roshan_timer.check_and_announce()
            await self.glyph_timer.check_and_announce()
            await self.tormentor_timer.check_and_announce()
            await self.mindful_timer.check_and_announce()

        except asyncio.CancelledError:
            logger.info(f"Timer loop for guild {self.guild_id} cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in timer_loop: {e}", exc_info=True)

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in list(self.static_events.items()):
            if self.time_elapsed == event["time"]:
                message = event['message']
                await self.announcement_manager.announce(self, message)
                del self.static_events[event_id]
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self):
        """Check and trigger periodic events."""
        for event_id, event in self.periodic_events.items():
            if event["start_time"] <= self.time_elapsed <= event["end_time"]:
                if (self.time_elapsed - event["start_time"]) % event["interval"] == 0:
                    message = event['message']
                    await self.announcement_manager.announce(self, message)
                    logger.info(f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")

    def is_running(self):
        return self.running and self.timer_task.is_running()

    def is_paused(self):
        return self.paused

    def close(self):
        self.events_manager.close()
        logger.debug(f"GameTimer for guild ID {self.guild_id} closed.")
