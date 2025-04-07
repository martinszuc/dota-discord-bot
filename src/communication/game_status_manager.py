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
            embed = discord.Embed(
                title="Dota Timer Bot Status",
                description="Initializing game timer...",
                color=0x2E7D32  # Green color
            )

            embed.add_field(name="Status", value="⏱️ Starting...", inline=False)
            embed.add_field(name="Mode", value=mode.capitalize(), inline=True)
            embed.set_footer(text="Game timer will update shortly")

            self.status_message = await channel.send(embed=embed)
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
            timer_status = f"⏱️ Countdown: **{minutes:02d}:{seconds:02d}**"
            description = "Game will start soon"
            color = 0xFFA726  # Orange color for countdown
        else:
            # Elapsed time format
            minutes = time_elapsed // 60
            seconds = time_elapsed % 60
            timer_status = f"⏱️ Game Time: **{minutes:02d}:{seconds:02d}**"
            description = "Game in progress"
            color = 0x2E7D32  # Green color for active game

        # Add paused indicator
        if paused:
            timer_status += " (⏸️ Paused)"
            description += " (Paused)"
            color = 0x757575  # Gray color for paused game

        # Format recent events with emojis for better visibility
        events_str = ""
        if recent_events:
            for i, event in enumerate(recent_events):
                # Add emoji based on event content
                if "Roshan" in event:
                    emoji = "🛡️"
                elif "Glyph" in event:
                    emoji = "🔮"
                elif "Tormentor" in event:
                    emoji = "🐉"
                elif "Bounty" in event or "Rune" in event:
                    emoji = "💎"
                elif "neutral" in event.lower():
                    emoji = "📦"
                else:
                    emoji = "📢"

                # Add the event with emoji and proper formatting
                events_str += f"{emoji} {event}\n"
        else:
            events_str = "No recent events."

        # Create updated embed content
        embed = discord.Embed(
            title=f"Dota Timer Bot - {mode.capitalize()} Mode",
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="Timer", value=timer_status, inline=False)
        embed.add_field(name="Recent Events", value=events_str, inline=False)

        # Add additional footer info
        footer_text = f"Use !bot-help for commands | Game Mode: {mode.capitalize()}"
        embed.set_footer(text=footer_text)

        try:
            await self.status_message.edit(embed=embed)
            logger.debug(f"Status message (ID: {self.status_message.id}) updated successfully.")
        except discord.DiscordException as e:
            logger.error(f"Failed to edit status message: {e}", exc_info=True)