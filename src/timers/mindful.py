# src/timers/mindful.py

import asyncio
import random
from communication.announcement import Announcement
from src.timers.base import BaseTimer
from src.utils.config import logger
from src.event_definitions import mindful_messages

class MindfulTimer(BaseTimer):
    """Class to manage the periodic mindful message announcements at random intervals."""

    def __init__(self, game_timer, min_interval=600, max_interval=900):  # Random interval between 10 and 15 minutes
        super().__init__(game_timer)
        self.announcement = Announcement()
        self.min_interval = min_interval
        self.max_interval = max_interval
        logger.debug(f"MindfulTimer initialized for guild ID {self.game_timer.guild_id} with interval range {self.min_interval}-{self.max_interval} seconds.")

    async def _run_timer(self, channel):
        """Send a random mindful message at random intervals while enabled."""
        logger.info(f"MindfulTimer running for guild ID {self.game_timer.guild_id}.")
        try:
            while self.is_running:
                if not self.game_timer.events_manager.mindful_messages_enabled(self.game_timer.guild_id):
                    logger.debug(f"Mindful messages are disabled for guild ID {self.game_timer.guild_id}. Waiting before next check.")
                    await asyncio.sleep(self.max_interval)  # Wait longer if messages are disabled
                    continue

                # Choose a random message and announce it
                message = random.choice(mindful_messages)["message"]
                await self.announcement.announce(self.game_timer, message)
                logger.info(f"Mindful message sent in guild ID {self.game_timer.guild_id}: '{message}'")

                # Wait for a random interval between min_interval and max_interval before sending the next message
                random_interval = random.randint(self.min_interval, self.max_interval)
                logger.debug(f"MindfulTimer will wait for {random_interval} seconds before next message.")
                await asyncio.sleep(random_interval)

        except asyncio.CancelledError:
            logger.info(f"MindfulTimer task cancelled for guild ID {self.game_timer.guild_id}.")
        finally:
            self.is_running = False
            logger.debug(f"MindfulTimer concluded for guild ID {self.game_timer.guild_id}.")
