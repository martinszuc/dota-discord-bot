import asyncio
from discord.ext import tasks
from events import EVENTS, PERIODIC_EVENTS
from utils import mention_players, parse_time

class GameTimer:
    def __init__(self):
        self.time_elapsed = 0
        self.task = None
        self.channel = None
        self.usernames = []
        self.custom_periodic_events = []

    async def start(self, ctx, countdown, usernames):
        self.channel = ctx.channel
        self.time_elapsed = -countdown
        self.usernames = usernames
        self.task = self.timer_task.start()

    async def stop(self):
        if self.task:
            self.timer_task.cancel()
            self.task = None
            self.time_elapsed = 0
            self.custom_periodic_events.clear()

    def add_periodic_event(self, start_time, interval, end_time, message, target_groups):
        event = {
            "start_time": parse_time(start_time),
            "interval": parse_time(interval),
            "end_time": parse_time(end_time),
            "message": message,
            "target_groups": target_groups
        }
        self.custom_periodic_events.append(event)

    def remove_event(self, message):
        self.custom_periodic_events = [
            event for event in self.custom_periodic_events if event["message"] != message
        ]

    @tasks.loop(seconds=1)
    async def timer_task(self):
        self.time_elapsed += 1
        await self.check_events()
        await self.check_periodic_events()
        await self.check_custom_periodic_events()

    async def check_events(self):
        for event_time, (message, target_groups) in EVENTS.items():
            if self.time_elapsed == parse_time(event_time):
                mentions = mention_players(target_groups, self.usernames)
                await self.channel.send(f"{message} {mentions}")

    async def check_periodic_events(self):
        for start_time, interval, end_time, (message, target_groups) in PERIODIC_EVENTS:
            start_seconds = parse_time(start_time)
            interval_seconds = parse_time(interval)
            end_seconds = parse_time(end_time)

            if start_seconds <= self.time_elapsed <= end_seconds and (self.time_elapsed - start_seconds) % interval_seconds == 0:
                mentions = mention_players(target_groups, self.usernames)
                await self.channel.send(f"{message} {mentions}")

    async def check_custom_periodic_events(self):
        for event in self.custom_periodic_events:
            start_seconds = event["start_time"]
            interval_seconds = event["interval"]
            end_seconds = event["end_time"]

            if start_seconds <= self.time_elapsed <= end_seconds and (self.time_elapsed - start_seconds) % interval_seconds == 0:
                mentions = mention_players(event["target_groups"], self.usernames)
                await self.channel.send(f"{event['message']} {mentions}")
