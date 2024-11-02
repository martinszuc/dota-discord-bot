import asyncio
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
        self.timer_task = self._timer_task.start()
        self.auto_stop_task = self._auto_stop_task.start()

    async def stop(self):
        """Stop the game timer."""
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
        if self.auto_stop_task:
            self.auto_stop_task.cancel()
            self.auto_stop_task = None
        self.time_elapsed = 0
        self.custom_events.clear()

    def is_running(self):
        """Check if the timer is running."""
        return self.timer_task is not None and self.timer_task.is_running()

    def add_custom_event(self, start_time, interval, end_time, message, target_groups):
        """Add a custom periodic event."""
        event = {
            "start_time": parse_time(start_time),
            "interval": parse_time(interval),
            "end_time": parse_time(end_time),
            "message": message,
            "target_groups": target_groups
        }
        self.custom_events.append(event)

    def remove_custom_event(self, message):
        """Remove a custom periodic event by message."""
        self.custom_events = [event for event in self.custom_events if event["message"] != message]

    def get_custom_events(self):
        """Get all custom periodic events."""
        return self.custom_events

    @tasks.loop(seconds=1)
    async def _timer_task(self):
        """Main timer loop that checks events every second."""
        self.time_elapsed += 1
        await self._check_events()
        await self._check_periodic_events()
        await self._check_custom_events()

    @tasks.loop(seconds=1)
    async def _auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:  # 1.5 hours in seconds
            await self.stop()
            await self.channel.send("Game timer automatically stopped after 1.5 hours.")

    async def _check_events(self):
        """Check and trigger static events."""
        for event_time, (message, target_groups) in EVENTS.items():
            if self.time_elapsed == parse_time(event_time):
                mentions = mention_players(target_groups, self.usernames)
                await self.channel.send(f"{message} {mentions}")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for start_time, interval, end_time, (message, target_groups) in PERIODIC_EVENTS:
            start_seconds = parse_time(start_time)
            interval_seconds = parse_time(interval)
            end_seconds = parse_time(end_time)
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(target_groups, self.usernames)
                    await self.channel.send(f"{message} {mentions}")

    async def _check_custom_events(self):
        """Check and trigger custom periodic events."""
        for event in self.custom_events:
            start_seconds = event["start_time"]
            interval_seconds = event["interval"]
            end_seconds = event["end_time"]
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(event["target_groups"], self.usernames)
                    await self.channel.send(f"{event['message']} {mentions}")
