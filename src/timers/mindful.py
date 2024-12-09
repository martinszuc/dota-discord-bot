# src/timers/mindful.py

import random
from src.timers.base import BaseTimer
from src.event_definitions import mindful_messages, mindful_pre_messages
from src.utils.config import logger

class MindfulTimer(BaseTimer):
    """Manages periodic mindful message announcements."""

    def __init__(self, game_timer, min_interval=600, max_interval=900, audio_chance=0.07):
        super().__init__(game_timer)
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.audio_chance = audio_chance
        self.next_trigger_time = None
        self.enabled = False
        logger.debug(f"MindfulTimer initialized with intervals {self.min_interval}-{self.max_interval} seconds and audio chance {self.audio_chance}.")

    def enable(self):
        """Enable mindful messages."""
        if not self.enabled:
            self.enabled = True
            self.schedule_next()
            logger.info(f"MindfulTimer enabled for guild ID {self.game_timer.guild_id}.")

    def disable(self):
        """Disable mindful messages."""
        if self.enabled:
            self.enabled = False
            self.next_trigger_time = None
            logger.info(f"MindfulTimer disabled for guild ID {self.game_timer.guild_id}.")

    def setup(self):
        """Initial setup if needed."""
        pass  # MindfulTimer doesn't require initial setup beyond initialization

    def schedule_next(self):
        """Schedule the next mindful message."""
        if not self.enabled:
            return
        current_time = self.game_timer.time_elapsed
        interval = random.randint(self.min_interval, self.max_interval)
        self.next_trigger_time = current_time + interval
        logger.debug(f"MindfulTimer scheduled next message at {self.next_trigger_time} seconds.")

    async def check_and_announce(self):
        if not self.enabled or not self.game_timer.is_running():
            return

        current_time = self.game_timer.time_elapsed
        if self.next_trigger_time is not None and current_time == self.next_trigger_time:
            # Decide between text or audio
            if random.random() < self.audio_chance and self.game_timer.voice_client and self.game_timer.voice_client.is_connected():
                # Play audio with TTS intro
                message = random.choice(mindful_pre_messages)["message"]
                await self.announcement.announce(self.game_timer, message)
                audio_message = random.choice(mindful_messages)["message"]
                await self.announcement.announce(self.game_timer, audio_message)
                logger.info(f"MindfulTimer played audio message: '{audio_message}'")
            else:
                # Send text message
                message = random.choice(mindful_messages)["message"]
                await self.announcement.announce(self.game_timer, message)
                logger.info(f"MindfulTimer sent text message: '{message}'")

            # Schedule next
            self.schedule_next()
