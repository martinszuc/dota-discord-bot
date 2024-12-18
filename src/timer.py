import asyncio

from discord.ext import tasks

from src.communication.announcement import Announcement
from src.communication.game_status_manager import GameStatusMessageManager
from src.managers.event_manager import EventsManager
from src.timers.glyph import GlyphTimer
from src.timers.mindful import MindfulTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer
from src.utils.config import logger
from src.utils.utils import parse_initial_countdown


class GameTimer:
    """
    Manages the overall game timer and coordinates various event timers.

    Attributes:
        guild_id (int): Unique identifier for the Discord guild/server.
        mode (str): Game mode ('regular' or 'turbo').
        time_elapsed (int): Total time elapsed since the timer started, in seconds.
        channel (discord.TextChannel): Discord text channel for sending announcements.
        paused (bool): Indicates if the timer is currently paused.
        pause_event (asyncio.Event): Event to handle pausing and resuming.
        announcement_manager (Announcement): Instance to manage announcements.
        status_manager (GameStatusMessageManager): Manages the dynamic status message.
        events_manager (EventsManager): Instance to manage event data.
        roshan_timer (RoshanTimer): Timer for Roshan's respawn.
        glyph_timer (GlyphTimer): Timer for Glyph cooldowns.
        tormentor_timer (TormentorTimer): Timer for Tormentor's respawn.
        mindful_timer (MindfulTimer): Timer for sending mindful messages.
        static_events (dict): Static events loaded for the guild.
        periodic_events (dict): Periodic events loaded for the guild.
        recent_events (list): List of recent event descriptions.
    """

    def __init__(self, guild_id: int, mode: str = 'regular'):
        """
        Initialize the GameTimer with guild-specific settings.

        Args:
            guild_id (int): The Discord guild/server ID.
            mode (str, optional): The game mode. Defaults to 'regular'.
        """
        self.guild_id = guild_id
        self.mode = mode
        self.time_elapsed = 0
        self.channel = None
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused

        self.announcement_manager = Announcement()
        self.recent_events = []
        self.status_manager = GameStatusMessageManager()  # Instantiate the manager
        self.events_manager = EventsManager()

        # Instantiate child timers without starting them automatically, except for mindful_timer.
        self.roshan_timer = RoshanTimer(self)
        self.glyph_timer = GlyphTimer(self)
        self.tormentor_timer = TormentorTimer(self)
        self.mindful_timer = MindfulTimer(self)

        self.static_events = {}
        self.periodic_events = {}

    async def start(self, channel: 'discord.TextChannel', countdown: str) -> None:
        """
        Start the game timer with an initial countdown.

        Args:
            channel (discord.TextChannel): The channel where announcements will be sent.
            countdown (str): Initial countdown time (e.g., "45" or "-10:00 turbo").
        """
        self.channel = channel
        self.paused = False
        self.pause_event.set()

        # Initialize status message
        await self.status_manager.create_status_message(channel, self.mode)

        # Parse the initial countdown to set the elapsed time.
        self.time_elapsed = parse_initial_countdown(countdown)
        logger.info(f"Game timer parsed countdown '{countdown}' -> time_elapsed={self.time_elapsed} seconds.")

        # Load event definitions for the guild and specified mode.
        self.static_events = self.events_manager.get_static_events(self.guild_id, self.mode)
        self.periodic_events = self.events_manager.get_periodic_events(self.guild_id, self.mode)
        logger.debug(f"Loaded static/periodic events for guild ID {self.guild_id} in mode '{self.mode}'.")

        # Start the main timer loop if it's not already running.
        if not self.timer_task.is_running():
            self.timer_task.start()
            logger.info("GameTimer main loop started.")
        else:
            logger.debug("GameTimer main loop is already running, skipping restart.")

        # Start only the mindful timer automatically upon game start.
        await self.mindful_timer.start(channel)
        logger.debug("MindfulTimer started automatically upon game start.")

    async def stop(self) -> None:
        """
        Stop the game timer and all associated child timers.
        """
        logger.info(f"Stopping GameTimer for guild ID {self.guild_id}.")
        self.timer_task.cancel()
        self.paused = False
        self.status_manager.status_message = None
        await self._stop_all_child_timers()
        logger.info(f"GameTimer and all child timers stopped for guild ID {self.guild_id}.")

    async def pause(self) -> None:
        """
        Pause the game timer and all associated child timers.
        """
        logger.info(f"Pausing GameTimer for guild ID {self.guild_id}.")
        self.paused = True
        self.pause_event.clear()
        await self._pause_all_child_timers()
        logger.info(f"GameTimer and all child timers paused for guild ID {self.guild_id}.")

        # Update the status message to reflect the paused state
        await self.status_manager.update_status_message(
            time_elapsed=self.time_elapsed,
            mode=self.mode,
            recent_events=self.recent_events,
            paused=self.paused
        )

    async def unpause(self) -> None:
        """
        Resume the game timer and all associated child timers if they were paused.
        """
        logger.info(f"Unpausing GameTimer for guild ID {self.guild_id}.")
        self.paused = False
        self.pause_event.set()
        await self._resume_all_child_timers()
        logger.info(f"GameTimer and all child timers resumed for guild ID {self.guild_id}.")

        # Update the status message to reflect the resumed state
        await self.status_manager.update_status_message(
            time_elapsed=self.time_elapsed,
            mode=self.mode,
            recent_events=self.recent_events,
            paused=self.paused
        )

    @tasks.loop(seconds=1)
    async def timer_task(self) -> None:
        """
        Main timer loop that increments the elapsed time every second and checks for event triggers.
        """
        try:
            if self.paused:
                await self.pause_event.wait()

            # Handle countdown and elapsed time logic
            if self.time_elapsed < 0:
                self.time_elapsed += 1  # Countdown
            else:
                self.time_elapsed += 1  # Elapsed game time

            logger.debug(f"Time elapsed: {self.time_elapsed} seconds (guild_id={self.guild_id})")

            # Check and trigger both static and periodic events if the game has started
            if self.time_elapsed >= 0:
                await self._check_static_events()
                await self._check_periodic_events()

            # Update the status message via the manager
            await self.status_manager.update_status_message(
                time_elapsed=self.time_elapsed,
                mode=self.mode,
                recent_events=self.recent_events,
                paused=self.paused
            )
        except asyncio.CancelledError:
            logger.info(f"GameTimer loop cancelled for guild ID {self.guild_id}.")
        except Exception as e:
            logger.error(f"Unexpected error in GameTimer loop for guild ID {self.guild_id}: {e}", exc_info=True)

    async def _check_static_events(self) -> None:
        """
        Check and trigger static events based on the elapsed time.
        """
        for event_id, event in self.static_events.items():
            if self.time_elapsed == event["time"]:
                message = event['message']
                logger.info(
                    f"Triggering static event ID {event_id} for guild ID {self.guild_id}: '{message}' at {self.time_elapsed} seconds.")
                await self.announcement_manager.announce(self, message)
                self.add_recent_event(f"{ message}")
                logger.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{message}'")

    async def _check_periodic_events(self) -> None:
        """
        Check and trigger periodic events based on the elapsed time.
        """
        for event_id, event in self.periodic_events.items():
            if event["start_time"] <= self.time_elapsed <= event["end_time"]:
                if (self.time_elapsed - event["start_time"]) % event["interval"] == 0:
                    message = event['message']
                    logger.info(
                        f"Triggering periodic event ID {event_id} for guild ID {self.guild_id}: '{message}' at {self.time_elapsed} seconds.")
                    await self.announcement_manager.announce(self, message)
                    self.add_recent_event(f"{ message}")
                    logger.info(
                        f"Periodic event triggered: ID={event_id}, message='{message}', interval={event['interval']}")

    async def _stop_all_child_timers(self) -> None:
        """
        Stop all child timers (Roshan, Glyph, Tormentor, Mindful).
        """
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running:
                await timer.stop()

    async def _pause_all_child_timers(self) -> None:
        """
        Pause all child timers (Roshan, Glyph, Tormentor, Mindful).
        """
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and not timer.is_paused:
                await timer.pause()

    async def _resume_all_child_timers(self) -> None:
        """
        Resume all child timers (Roshan, Glyph, Tormentor, Mindful) if they were paused.
        """
        for timer in [self.roshan_timer, self.glyph_timer, self.tormentor_timer, self.mindful_timer]:
            if timer.is_running and timer.is_paused:
                await timer.resume()

    def is_running(self) -> bool:
        """
        Check if the main timer task is currently running.

        Returns:
            bool: True if the main timer loop is running, False otherwise.
        """
        return self.timer_task.is_running()

    def is_paused(self) -> bool:
        """
        Check if the game timer is currently paused.

        Returns:
            bool: True if the timer is paused, False otherwise.
        """
        return self.paused

    def add_recent_event(self, message: str):
        """
        Add a recent event description to the event list.

        Args:
            message (str): The event message to add.
        """
        timestamp = self._format_time()
        self.recent_events.append(f"{timestamp} - {message}")
        if len(self.recent_events) > 7:
            self.recent_events.pop(0)

    def _format_time(self) -> str:
        """
        Format the current elapsed time as MM:SS.

        Returns:
            str: Formatted time string.
        """
        minutes = self.time_elapsed // 60
        seconds = self.time_elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"