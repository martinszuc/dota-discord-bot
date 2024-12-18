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

        Args:
            time_elapsed (int): The total time elapsed in seconds.
            mode (str): The current game mode.
            recent_events (list): List of recent event strings.
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

        # Create updated embed content
        embed = discord.Embed(title="Game Timer Status", color=0x00FF00)
        embed.add_field(name="Timer", value=elapsed_str, inline=False)
        embed.add_field(name="Mode", value=mode.capitalize(), inline=False)
        embed.add_field(name="Recent Events", value=events_str, inline=False)

        try:
            await self.status_message.edit(embed=embed)
            logger.debug(f"Status message (ID: {self.status_message.id}) updated successfully.")
        except discord.DiscordException as e:
            logger.error(f"Failed to edit status message: {e}", exc_info=True)