import asyncio
import logging
from discord.ext import tasks
from utils import mention_players, parse_time
from events import EVENTS, PERIODIC_EVENTS

class GameTimer:
    """Class to manage the game timer and events."""
    def __init__(self):
        self.time_elapsed = 0
        self.timer_task = None
        self.channel = None
        self.usernames = []
        self.custom_events = []
        self.auto_stop_task = None

    async def start(self, channel, countdown, usernames):
        """Start the game timer."""
        self.channel = channel
        self.time_elapsed = -countdown
        self.usernames = usernames
        logging.info(f"Game timer started with countdown={countdown} seconds and usernames={usernames}")
        self.timer_task = self._timer_task.start()
        self.auto_stop_task = self._auto_stop_task.start()

    async def stop(self):
        """Stop the game timer."""
        if self.timer_task:
            self.timer_task.cancel()
            logging.info("Game timer task canceled.")
            self.timer_task = None
        if self.auto_stop_task:
            self.auto_stop_task.cancel()
            logging.info("Auto-stop task canceled.")
            self.auto_stop_task = None
        self.time_elapsed = 0
        self.custom_events.clear()
        logging.info("Game timer stopped and all custom events cleared.")
        await self.channel.send("🛑 Game timer has been stopped and all events have been cleared.")

    def is_running(self):
        """Check if the timer is running."""
        return self.timer_task is not None and self.timer_task.is_running()

    def add_event(self, start_time, message, target_group):
        """Add a static event."""
        event_time = parse_time(start_time)
        if start_time in EVENTS:
            raise ValueError(f"❌ An event is already scheduled at {start_time}.")
        EVENTS[start_time] = (message, [target_group])
        logging.info(f"Static event added: time={start_time}, message='{message}', target_group='{target_group}'")

    def add_custom_event(self, start_time, interval, end_time, message, target_groups):
        """Add a custom periodic event."""
        start_seconds = parse_time(start_time)
        interval_seconds = parse_time(interval)
        end_seconds = parse_time(end_time)

        if interval_seconds <= 0:
            raise ValueError("❌ Interval must be greater than 0 seconds.")
        if end_seconds <= start_seconds:
            raise ValueError("❌ End time must be after start time.")

        event = {
            "start_time": start_seconds,
            "interval": interval_seconds,
            "end_time": end_seconds,
            "message": message,
            "target_groups": target_groups
        }
        self.custom_events.append(event)
        logging.info(f"Custom periodic event added: start_time={start_time}, interval={interval}, end_time={end_time}, message='{message}', target_groups={target_groups}")

    def remove_custom_event(self, message):
        """Remove a custom periodic event by message."""
        original_length = len(self.custom_events)
        self.custom_events = [event for event in self.custom_events if event["message"] != message]
        if len(self.custom_events) < original_length:
            logging.info(f"Custom event '{message}' removed.")
            return True
        else:
            logging.warning(f"Attempted to remove non-existent custom event '{message}'.")
            return False

    def get_custom_events(self):
        """Get all custom periodic events."""
        return self.custom_events

    @tasks.loop(seconds=1)
    async def _timer_task(self):
        """Main timer loop that checks events every second."""
        self.time_elapsed += 1
        logging.debug(f"Time elapsed: {self.time_elapsed} seconds")
        await self._check_events()
        await self._check_periodic_events()
        await self._check_custom_events()

    @tasks.loop(seconds=1)
    async def _auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:  # 1.5 hours in seconds
            await self.stop()
            logging.info("Game timer automatically stopped after 1.5 hours.")
            await self.channel.send("🛑 Game timer automatically stopped after 1.5 hours.")

    async def _check_events(self):
        """Check and trigger static events."""
        for event_time_str, (message, target_groups) in EVENTS.items():
            event_time = parse_time(event_time_str)
            if self.time_elapsed == event_time:
                mentions = mention_players(target_groups, self.usernames)
                await self.channel.send(f"📢 {message} {mentions}")
                logging.info(f"Static event triggered: time={event_time_str}, message='{message}', target_groups={target_groups}")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for start_time, interval, end_time, (message, target_groups) in PERIODIC_EVENTS:
            start_seconds = parse_time(start_time)
            interval_seconds = parse_time(interval)
            end_seconds = parse_time(end_time)
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(target_groups, self.usernames)
                    await self.channel.send(f"🔄 {message} {mentions}")
                    logging.info(f"Periodic event triggered: message='{message}', interval={interval}")

    async def _check_custom_events(self):
        """Check and trigger custom periodic events."""
        for event in self.custom_events:
            start_seconds = event["start_time"]
            interval_seconds = event["interval"]
            end_seconds = event["end_time"]
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(event["target_groups"], self.usernames)
                    await self.channel.send(f"🔁 {event['message']} {mentions}")
                    logging.info(f"Custom periodic event triggered: message='{event['message']}', interval={event['interval']}")