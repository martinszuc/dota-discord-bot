# timer.py

import asyncio
import logging
from discord.ext import tasks
from utils import mention_players, parse_time
from events import STATIC_EVENTS, PERIODIC_EVENTS

class GameTimer:
    """Class to manage the game timer and events."""
    def __init__(self):
        self.time_elapsed = 0
        self.timer_task = None
        self.channel = None
        self.usernames = []
        self.custom_events = {}
        self.auto_stop_task = None
        self.next_event_id = max(list(STATIC_EVENTS.keys()) + list(PERIODIC_EVENTS.keys()), default=0) + 1

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
        """Add a static event with a unique ID."""
        event_time = parse_time(start_time)
        # Check for duplicate event times in STATIC_EVENTS
        for event in STATIC_EVENTS.values():
            if event["time"] == start_time and event["message"] == message:
                raise ValueError(f"❌ An event with message '{message}' at time '{start_time}' already exists.")
        # Assign a unique ID
        event_id = self.next_event_id
        STATIC_EVENTS[event_id] = {"time": start_time, "message": message, "target_groups": [target_group]}
        self.next_event_id += 1
        logging.info(f"Static event added: ID={event_id}, time={start_time}, message='{message}', target_group='{target_group}'")
        return event_id

    def add_custom_event(self, start_time, interval, end_time, message, target_groups):
        """Add a custom periodic event with a unique ID."""
        start_seconds = parse_time(start_time)
        interval_seconds = parse_time(interval)
        end_seconds = parse_time(end_time)

        if interval_seconds <= 0:
            raise ValueError("❌ Interval must be greater than 0 seconds.")
        if end_seconds <= start_seconds:
            raise ValueError("❌ End time must be after start time.")

        event_id = self.next_event_id
        self.custom_events[event_id] = {
            "start_time": start_seconds,
            "interval": interval_seconds,
            "end_time": end_seconds,
            "message": message,
            "target_groups": target_groups
        }
        self.next_event_id += 1
        logging.info(f"Custom periodic event added: ID={event_id}, start_time={start_time}, interval={interval}, end_time={end_time}, message='{message}', target_groups={target_groups}")
        return event_id

    def remove_custom_event(self, event_id):
        """Remove a custom periodic event by its unique ID."""
        if event_id in self.custom_events:
            del self.custom_events[event_id]
            logging.info(f"Custom event ID {event_id} removed.")
            return True
        else:
            logging.warning(f"Attempted to remove non-existent custom event ID {event_id}.")
            return False

    def get_custom_events(self):
        """Get all custom periodic events."""
        return self.custom_events

    @tasks.loop(seconds=1)
    async def _timer_task(self):
        """Main timer loop that checks events every second."""
        self.time_elapsed += 1
        logging.debug(f"Time elapsed: {self.time_elapsed} seconds")
        await self._check_static_events()
        await self._check_periodic_events()
        await self._check_custom_events()

    @tasks.loop(seconds=1)
    async def _auto_stop_task(self):
        """Automatically stop the game after 1.5 hours."""
        if self.time_elapsed >= 90 * 60:  # 1.5 hours in seconds
            await self.stop()
            logging.info("Game timer automatically stopped after 1.5 hours.")
            await self.channel.send("🛑 Game timer automatically stopped after 1.5 hours.")

    async def _check_static_events(self):
        """Check and trigger static events."""
        for event_id, event in STATIC_EVENTS.items():
            event_time = parse_time(event["time"])
            if self.time_elapsed == event_time:
                mentions = mention_players(event["target_groups"], self.usernames)
                await self.channel.send(f"📢 {event['message']} {mentions}")
                logging.info(f"Static event triggered: ID={event_id}, time={event['time']}, message='{event['message']}', target_groups={event['target_groups']}")

    async def _check_periodic_events(self):
        """Check and trigger predefined periodic events."""
        for event_id, event in PERIODIC_EVENTS.items():
            start_seconds = parse_time(event["start_time"])
            interval_seconds = parse_time(event["interval"])
            end_seconds = parse_time(event["end_time"])
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(event["target_groups"], self.usernames)
                    await self.channel.send(f"🔄 {event['message']} {mentions}")
                    logging.info(f"Predefined periodic event triggered: ID={event_id}, message='{event['message']}', interval={event['interval']}")

    async def _check_custom_events(self):
        """Check and trigger custom periodic events."""
        for event_id, event in self.custom_events.items():
            start_seconds = event["start_time"]
            interval_seconds = event["interval"]
            end_seconds = event["end_time"]
            if start_seconds <= self.time_elapsed <= end_seconds:
                if (self.time_elapsed - start_seconds) % interval_seconds == 0:
                    mentions = mention_players(event["target_groups"], self.usernames)
                    await self.channel.send(f"🔁 {event['message']} {mentions}")
                    logging.info(f"Custom periodic event triggered: ID={event_id}, message='{event['message']}', interval={event['interval']}")

    async def start_glyph_timer(self, channel):
        """Start a 5-minute timer for the enemy's glyph cooldown."""
        glyph_cooldown = 5 * 60  # 5 minutes in seconds
        await asyncio.sleep(glyph_cooldown - 30)  # Notify 30 seconds before cooldown ends
        await channel.send("🛡️ **Enemy glyph available in 30 seconds!**")
        await asyncio.sleep(30)
        await channel.send("🛡️ **Enemy glyph cooldown has ended!**")
        logging.info("Enemy glyph cooldown ended.")
