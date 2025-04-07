import asyncio
import traceback
from typing import List, Tuple, Optional, Callable, Any

from src.utils.config import logger


class BaseTimer:
    """
    Enhanced abstract base class for Dota timers with robust pause, resume, and stop functionality.

    This class provides the foundational structure for specific game timers,
    handling common operations such as starting, pausing, resuming, and stopping the timer.
    It includes improved error handling, recovery mechanisms, and state tracking.
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
        self.start_time = None  # When the timer was started
        self.pause_start_time = None  # When the timer was last paused
        self.total_pause_duration = 0  # Total time spent paused
        self.task = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused
        self._error_count = 0  # Track consecutive errors
        self._max_errors = 3  # Maximum consecutive errors before recovery
        self._recovery_attempts = 0  # Track recovery attempts
        self._max_recovery_attempts = 2  # Maximum recovery attempts
        self._cleanup_callbacks = []  # Callbacks to run on timer cleanup
        logger.debug(f"{self.__class__.__name__} initialized for guild ID {self.game_timer.guild_id}.")

    async def start(self, channel: any) -> None:
        """
        Start the timer task asynchronously with improved error handling.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        if self.is_running:
            logger.warning(f"{self.__class__.__name__} is already running for guild ID {self.game_timer.guild_id}.")
            return

        self.is_running = True
        self.is_paused = False
        self.start_time = asyncio.get_event_loop().time()
        self.total_pause_duration = 0
        self.pause_event.set()
        self._error_count = 0
        self._recovery_attempts = 0

        # Create task with error handling
        self.task = asyncio.create_task(self._run_timer_with_error_handling(channel))
        logger.info(f"{self.__class__.__name__} started for guild ID {self.game_timer.guild_id}.")

    async def _run_timer_with_error_handling(self, channel: any) -> None:
        """
        Wrapper around _run_timer that provides error handling and recovery.

        Args:
            channel: The Discord channel where announcements will be sent.
        """
        try:
            # Run the timer implementation from the subclass
            await self._run_timer(channel)
        except asyncio.CancelledError:
            # Handle normal cancellation
            logger.info(f"{self.__class__.__name__} task cancelled for guild ID {self.game_timer.guild_id}.")
            # Clean up resources
            await self._execute_cleanup_callbacks()
            self.is_running = False
        except Exception as e:
            # Handle unexpected errors
            error_trace = traceback.format_exc()
            logger.error(
                f"Error in {self.__class__.__name__} for guild ID {self.game_timer.guild_id}: {e}\n{error_trace}")

            self._error_count += 1

            # Attempt recovery if we haven't exceeded the maximum errors or recovery attempts
            if self._error_count <= self._max_errors and self._recovery_attempts < self._max_recovery_attempts:
                logger.warning(
                    f"Attempting to recover {self.__class__.__name__} for guild ID {self.game_timer.guild_id}. "
                    f"Error count: {self._error_count}, Recovery attempt: {self._recovery_attempts + 1}")

                self._recovery_attempts += 1

                # Pause briefly before recovery
                await asyncio.sleep(1)

                # Try to restart the timer
                self.task = asyncio.create_task(self._run_timer_with_error_handling(channel))
            else:
                # Too many errors or recovery attempts, stop the timer
                logger.error(f"Stopping {self.__class__.__name__} for guild ID {self.game_timer.guild_id} "
                             f"after {self._error_count} errors and {self._recovery_attempts} recovery attempts.")

                # Notify channel of the error if possible
                try:
                    await channel.send(
                        f"⚠️ {self.__class__.__name__} stopped due to errors. Use the appropriate command to restart it.")
                except Exception as channel_err:
                    logger.error(f"Could not send error message to channel: {channel_err}")

                # Clean up resources
                await self._execute_cleanup_callbacks()
                self.is_running = False

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
        Pause the timer with time tracking.

        If the timer is running and not already paused, it will be paused.
        The pause start time is recorded for accurate timing.
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.pause_start_time = asyncio.get_event_loop().time()
            self.pause_event.clear()
            logger.info(f"{self.__class__.__name__} paused for guild ID {self.game_timer.guild_id}.")

    async def resume(self) -> None:
        """
        Resume the timer if it is paused, with accurate time tracking.

        If the timer is running and currently paused, it will resume.
        The pause duration is calculated and added to the total pause time.
        """
        if self.is_running and self.is_paused:
            current_time = asyncio.get_event_loop().time()

            # Calculate the duration of this pause period
            if self.pause_start_time is not None:
                pause_duration = current_time - self.pause_start_time
                self.total_pause_duration += pause_duration
                logger.debug(f"Pause duration: {pause_duration:.2f}s, Total paused: {self.total_pause_duration:.2f}s")

            self.is_paused = False
            self.pause_event.set()
            logger.info(f"{self.__class__.__name__} resumed for guild ID {self.game_timer.guild_id}.")

    async def stop(self) -> None:
        """
        Stop the timer and cancel the task if running.

        Resets the timer's state and ensures that any paused operations are unblocked.
        Runs cleanup callbacks to ensure proper resource management.
        """
        if not self.is_running:
            logger.debug(f"{self.__class__.__name__} is not running for guild ID {self.game_timer.guild_id}.")
            return

        logger.info(f"Stopping {self.__class__.__name__} for guild ID {self.game_timer.guild_id}.")

        # Set state before cancelling to avoid race conditions
        self.is_running = False
        self.is_paused = False
        self.pause_event.set()  # Unblock any paused operations

        if self.task:
            try:
                self.task.cancel()
                # Wait for task to fully cancel (with timeout)
                await asyncio.wait_for(asyncio.gather(self.task, return_exceptions=True), timeout=3.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout while waiting for {self.__class__.__name__} task to cancel.")
            except Exception as e:
                logger.error(f"Error while stopping {self.__class__.__name__}: {e}", exc_info=True)
            finally:
                self.task = None
                # Execute cleanup callbacks separately
                await self._execute_cleanup_callbacks()

        logger.info(f"{self.__class__.__name__} stopped for guild ID {self.game_timer.guild_id}.")

    async def sleep_with_pause(self, duration: float) -> bool:
        """
        Sleep for the specified duration, respecting pause state.

        This method allows the timer to be paused and resumed during the sleep period.
        Returns True if completed normally, False if interrupted.

        Args:
            duration (float): The total duration to sleep in seconds.

        Returns:
            bool: True if completed normally, False if interrupted
        """
        if duration <= 0:
            return True

        try:
            start_time = asyncio.get_event_loop().time()
            elapsed = 0

            while elapsed < duration and self.is_running:
                # Wait for pause event to be set (timer not paused)
                await self.pause_event.wait()

                # Sleep a small increment (make it responsive to pause/cancel)
                sleep_duration = min(0.5, duration - elapsed)
                await asyncio.sleep(sleep_duration)

                # Only count elapsed time when not paused
                if not self.is_paused:
                    current_time = asyncio.get_event_loop().time()
                    # Add time since last check
                    elapsed += current_time - (start_time + elapsed)

            return self.is_running  # Return True if still running
        except asyncio.CancelledError:
            logger.debug(f"sleep_with_pause cancelled in {self.__class__.__name__}")
            return False

    async def schedule_warnings(self, warnings_list: List[Tuple[float, str]], announcement: any) -> None:
        """
        Handle repeated "sleep and announce" logic for scheduled warnings.

        Args:
            warnings_list (list): A list of tuples in the format [(delay_in_seconds, message), ...].
            announcement: An instance of Announcement to send messages.
        """
        for index, (delay, message) in enumerate(warnings_list):
            # For each warning, sleep and then announce if still running
            completed = await self.sleep_with_pause(delay)
            if not completed or not self.is_running:
                logger.debug(f"Warning schedule interrupted at index {index} in {self.__class__.__name__}")
                return  # Exit the loop if interrupted

            # Send announcement if timer is still running
            if self.is_running:
                try:
                    await announcement.announce(self.game_timer, message)
                    logger.info(f"Announced: '{message}' for {self.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Error announcing message '{message}': {e}", exc_info=True)
                    # Continue despite error - don't fail the whole schedule for one message

    def get_elapsed_time(self) -> float:
        """
        Calculate the elapsed time accounting for pauses.

        Returns:
            float: The elapsed time in seconds, accounting for pauses
        """
        if not self.start_time:
            return 0.0

        current_time = asyncio.get_event_loop().time()
        total_time = current_time - self.start_time

        # Add current pause duration if paused
        current_pause = 0
        if self.is_paused and self.pause_start_time:
            current_pause = current_time - self.pause_start_time

        # Return total time minus all paused time
        return total_time - self.total_pause_duration - current_pause

    def add_cleanup_callback(self, callback: Callable[[], Any]) -> None:
        """
        Add a callback function to be called when the timer is cleaned up.

        Args:
            callback: A function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)

    async def _execute_cleanup_callbacks(self) -> None:
        """Execute all registered cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}", exc_info=True)