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

    async def update_status_message(self, time_elapsed: int, mode: str, recent_events: list, paused: bool):
        """
        Update the existing status message with the current game timer state and recent events.

        Args:
            time_elapsed (int): The total time elapsed (or negative countdown) in seconds.
            mode (str): The current game mode.
            recent_events (list): List of recent event strings.
            paused (bool): Indicates if the game timer is paused.
        """
        if self.status_message is None:
            logger.warning("Status message does not exist. Cannot update.")
            return

        # Determine if the game has started
        if time_elapsed < 0:
            # Countdown format
            minutes = abs(time_elapsed) // 60
            seconds = abs(time_elapsed) % 60
            timer_status = f"Countdown: {minutes:02d}:{seconds:02d} (Game not started)"
        else:
            # Elapsed time format
            minutes = time_elapsed // 60
            seconds = time_elapsed % 60
            timer_status = f"Game Time: {minutes:02d}:{seconds:02d}"

        if paused:
            timer_status += " (Paused)"

        # Format recent events
        events_str = "\n".join(recent_events) if recent_events else "No recent events."

        # Create updated embed content
        embed = discord.Embed(title="Game Timer Status", color=0x00FF00)
        embed.add_field(name="Timer", value=timer_status, inline=False)
        embed.add_field(name="Mode", value=mode.capitalize(), inline=False)
        embed.add_field(name="Recent Events", value=events_str, inline=False)

        try:
            await self.status_message.edit(embed=embed)
            logger.debug(f"Status message (ID: {self.status_message.id}) updated successfully.")
        except discord.DiscordException as e:
            logger.error(f"Failed to edit status message: {e}", exc_info=True)
