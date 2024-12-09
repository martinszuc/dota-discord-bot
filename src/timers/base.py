# src/timers/base.py

import logging

from src.utils.config import logger

class BaseTimer:
    """Base class for child timers with setup, reset, and announce methods."""

    def __init__(self, game_timer):
        self.game_timer = game_timer
        self.is_running = False
        self.next_announcements = []
        self.announcement = self.game_timer.announcement_manager
        logger.debug(f"{self.__class__.__name__} initialized for guild ID {self.game_timer.guild_id}.")

    def setup(self):
        """Set up the timer based on the game mode and current time."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    def reset(self):
        """Reset the timer."""
        self.is_running = False
        self.next_announcements = []
        logger.info(f"{self.__class__.__name__} reset for guild ID {self.game_timer.guild_id}.")

    async def check_and_announce(self):
        """Check if any announcements need to be made based on time_elapsed."""
        raise NotImplementedError("This method should be implemented by subclasses.")
