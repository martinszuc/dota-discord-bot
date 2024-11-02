from datetime import datetime, timedelta
from discord.ext import tasks

class RoshanTimer:
    """Class to manage Roshan's respawn timer."""
    ROSH_RESPAWN_MSG = "RS maybe alive! worst case scenario is {}."

    def __init__(self):
        self.roshan_killed_time = None
        self.channel = None
        self.respawn_task = None

    async def start(self, channel):
        """Start the Roshan respawn timer."""
        self.roshan_killed_time = datetime.now()
        self.channel = channel
        if self.respawn_task and self.respawn_task.is_running():
            self.respawn_task.cancel()
        self.respawn_task = self._respawn_task.start()

    @tasks.loop(seconds=1)
    async def _respawn_task(self):
        """Timer loop for Roshan's respawn."""
        respawn_time = self.roshan_killed_time + timedelta(minutes=8)
        latest_respawn_time = self.roshan_killed_time + timedelta(minutes=11)
        if datetime.now() >= respawn_time:
            await self.channel.send(self.ROSH_RESPAWN_MSG.format(latest_respawn_time.strftime("%H:%M")))
            self.respawn_task.cancel()
