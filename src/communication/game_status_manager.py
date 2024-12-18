import discord
from src.utils.config import logger

class GameStatusMessageManager:
    """
    Handles the creation and updating of a dynamic status message in the timer-bot channel.
    This class abstracts all the presentation logic away from the GameTimer, keeping code clean and maintainable.
    """

    def __init__(self):
        self.status_message = None

    async def create_status_message(self, channel: discord.TextChannel, mode: str):
        """
        Create an initial status message in the given channel.
        Returns the created message instance.
        """
        # Initial placeholder message
        try:
            self.status_message = await channel.send("Initializing game status...")
            logger.info(f"Created a new status message (ID: {self.status_message.id}) in channel '{channel.name}'.")
            return self.status_message
        except discord.DiscordException as e:
            logger.error(f"Failed to create status message: {e}", exc_info=True)
            self.status_message = None
            return None

    async def update_status_message(self, time_elapsed: int, mode: str, recent_events: list):
        """
        Update the existing status message with the current game timer state and recent events.
        If the message does not exist, this function will fail silently or handle re-creation if desired.
        """
        if self.status_message is None:
            logger.warning("Status message does not exist. Cannot update.")
            return

        # Format elapsed time
        minutes = time_elapsed // 60
        seconds = time_elapsed % 60
        elapsed_str = f"{minutes:02d}:{seconds:02d}"

        # Format recent events
        events_str = "\n".join(recent_events) if recent_events else "No recent events."

        # Create updated content
        new_content = (
            f"**Game Timer**: {elapsed_str}\n"
            f"**Mode**: {mode}\n"
            f"**Recent Events**:\n{events_str}"
        )

        try:
            await self.status_message.edit(content=new_content)
            logger.debug(f"Status message (ID: {self.status_message.id}) updated successfully.")
        except discord.DiscordException as e:
            logger.error(f"Failed to edit status message: {e}", exc_info=True)
