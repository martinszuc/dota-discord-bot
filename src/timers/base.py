import asyncio

from src.utils.config import logger


class BaseTimer:
    """
    Abstract base class for Dota timers with pause, resume, and stop functionality.

    This class provides the foundational structure for specific game timers,
    handling common operations such as starting, pausing, resuming, and stopping the timer.
    """

    def __init__(self, game_timer):
        """
        Initialize the BaseTimer with a reference to the game timer.

        Args:
            game_timer: An instance containing game state and timer-related information.
        """
        self.game_timer = game_timer
        self.is_running = False
        self.is_paused = False
        self.task = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused
        logger.debug(f"{self.__class__.__name__} initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self, channel: any) -> None:
        """
        Start the timer task asynchronously.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.pause_event.set()
            self.task = asyncio.create_task(self._run_timer(channel))
            logger.info(f"{self.__class__.__name__} started for guild ID {self.game_timer.guild_id}.")
        else:
            logger.warning(f"{self.__class__.__name__} is already running.")

    async def _run_timer(self, channel: any) -> None:
        """
        Abstract method for timer countdown logic.

        Must be implemented by subclasses.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    async def pause(self) -> None:
        """
        Pause the timer.

        If the timer is running and not already paused, it will be paused.
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            logger.info(f"{self.__class__.__name__} paused for guild ID {self.game_timer.guild_id}.")

    async def resume(self) -> None:
        """
        Resume the timer if it is paused.

        If the timer is running and currently paused, it will resume.
        """
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            logger.info(f"{self.__class__.__name__} resumed for guild ID {self.game_timer.guild_id}.")

    async def stop(self) -> None:
        """
        Stop the timer and cancel the task if running.

        Resets the timer's state and ensures that any paused operations are unblocked.
        """
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.pause_event.set()  # Unblock any paused operations
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info(f"{self.__class__.__name__} task was cancelled for guild ID {self.game_timer.guild_id}.")
                self.task = None
            logger.info(f"{self.__class__.__name__} stopped for guild ID {self.game_timer.guild_id}.")

    async def sleep_with_pause(self, duration: float) -> None:
        """
        Sleep for the specified duration, respecting pause state.

        This method allows the timer to be paused and resumed during the sleep period.

        Args:
            duration (float): The total duration to sleep in seconds.
        """
        try:
            while duration > 0 and self.is_running:
                await self.pause_event.wait()
                sleep_duration = min(1, duration)
                await asyncio.sleep(sleep_duration)
                duration -= sleep_duration
        except asyncio.CancelledError:
            pass

    async def schedule_warnings(self, warnings_list: list, announcement: any) -> None:
        """
        Handle repeated "sleep and announce" logic for scheduled warnings.

        Args:
            warnings_list (list): A list of tuples in the format [(delay_in_seconds, message), ...].
            announcement: An instance of Announcement to send messages.
        """
        for delay, message in warnings_list:
            await self.sleep_with_pause(delay)
            if not self.is_running:
                return  # Exit the loop if the timer was stopped
            await announcement.announce(self.game_timer, message)
