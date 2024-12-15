# src/timers/base.py

import asyncio

from src.utils.config import logger


class BaseTimer:
    """Base class for Dota timers with pause, resume, and stop functionality."""

    def __init__(self, game_timer):
        self.game_timer = game_timer
        self.is_running = False
        self.is_paused = False
        self.task = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused
        logger.debug(f"{self.__class__.__name__} initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self, channel):
        """Start the timer task asynchronously."""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.pause_event.set()
            self.task = asyncio.create_task(self._run_timer(channel))
            logger.info(f"{self.__class__.__name__} started for guild ID {self.game_timer.guild_id}.")
        else:
            logger.warning(f"{self.__class__.__name__} is already running.")

    async def _run_timer(self, channel):
        """Internal method for timer countdown logic."""
        raise NotImplementedError("This method should be implemented by subclasses")

    async def pause(self):
        """Pause the timer."""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            logger.info(f"{self.__class__.__name__} paused for guild ID {self.game_timer.guild_id}.")

    async def resume(self):
        """Resume the timer if it is paused."""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            logger.info(f"{self.__class__.__name__} resumed for guild ID {self.game_timer.guild_id}.")

    async def stop(self):
        """Stop the timer and cancel the task if running."""
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.pause_event.set()  # Unblock any paused operations
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info(
                        f"{self.__class__.__name__} task was cancelled for guild ID {self.game_timer.guild_id}.")
                self.task = None
            logger.info(f"{self.__class__.__name__} stopped for guild ID {self.game_timer.guild_id}.")

    async def sleep_with_pause(self, duration):
        """Sleep for the specified duration, respecting pause."""
        try:
            while duration > 0 and self.is_running:
                await self.pause_event.wait()
                sleep_duration = min(1, duration)
                await asyncio.sleep(sleep_duration)
                duration -= sleep_duration
        except asyncio.CancelledError:
            pass

    async def schedule_warnings(self, warnings_list, announcement):
        """
        Helper method to handle repeated "sleep and announce" logic.

        :param warnings_list: A list of tuples: [(delay_in_seconds, message), ...]
        :param announcement: The Announcement() instance to use for sending messages.
        """
        for delay, message in warnings_list:
            await self.sleep_with_pause(delay)
            if not self.is_running:
                return  # If timer was stopped mid-way, exit the loop
            await announcement.announce(self.game_timer, message)
