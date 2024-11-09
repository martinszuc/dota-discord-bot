# src/timers/base.py

import asyncio
import logging

logger = logging.getLogger(__name__)

class BaseTimer:
    """Base class for Dota timers with pause, resume, and stop functionality."""

    def __init__(self, game_timer):
        self.game_timer = game_timer
        self.is_running = False
        self.is_paused = False
        self.task = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused

    async def start(self, channel):
        """Start the timer task asynchronously."""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.pause_event.set()
            self.task = asyncio.create_task(self._run_timer(channel))
            logger.info(f"{self.__class__.__name__} started.")
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
            logger.info(f"{self.__class__.__name__} paused.")

    async def resume(self):
        """Resume the timer if it is paused."""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            logger.info(f"{self.__class__.__name__} resumed.")

    async def stop(self):
        """Stop the timer and cancel the task if running."""
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info(f"{self.__class__.__name__} task was cancelled.")
                self.task = None
            logger.info(f"{self.__class__.__name__} stopped.")
