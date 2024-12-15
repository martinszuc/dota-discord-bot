import logging

import discord
from discord.ext import commands

from src.utils.config import PREFIX


class HelpCog(commands.Cog):
    """
    A Cog for handling the help command, providing users with information about available bot commands.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize the HelpCog with the bot instance.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        self.logger = logging.getLogger('DotaDiscordBot')
        self.prefix = PREFIX

    @commands.command(
        name="bot-help",
        aliases=['dota-help', 'dotahelp', 'pls', 'help'],
        brief="Displays the help message with available commands."
    )
    async def send_help(self, ctx: commands.Context) -> None:
        """
        Sends an embedded help message detailing all available commands and their usage.

        Args:
            ctx (commands.Context): The context in which the command was invoked.
        """
        self.logger.info(f"Command '!bot-help' invoked by {ctx.author} in guild ID {ctx.guild.id}")

        # Create an embed to structure the help message.
        embed = discord.Embed(
            title="Dota Timer Bot - Help",
            color=0x00ff00,
            description="List of available commands and their descriptions."
        )

        # Define command categories and their respective commands.
        categories = {
            "📅 **Game Timer**": [
                {
                    "name": f"{self.prefix}start <countdown> [mode]",
                    "value": "Starts the game timer.\n**Example:** `{0}start 45` or `{0}start -10:00 turbo`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}stop",
                    "value": "Stops the current game timer."
                },
                {
                    "name": f"{self.prefix}pause *(Alias: `p`)*",
                    "value": "Pauses the game timer and all events."
                },
                {
                    "name": f"{self.prefix}unpause *(Aliases: `unp`, `up`)*",
                    "value": "Resumes the game timer and all events."
                },
                {
                    "name": f"{self.prefix}killall",
                    "value": "Stops all active game timers across all guilds. *(Admin only)*"
                }
            ],
            "🛡️ **Roshan Timer**": [
                {
                    "name": f"{self.prefix}rosh *(Aliases: `rs`, `rsdead`, `rs-dead`, `rsdied`, `rs-died`)*",
                    "value": "Logs Roshan's death and starts the respawn timer.\n**Example:** `{0}rosh`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}cancel-rosh *(Aliases: `rsalive`, `rsback`, `rsb`)*",
                    "value": "Cancels the Roshan respawn timer if active.\n**Example:** `{0}cancel-rosh`".format(
                        self.prefix)
                }
            ],
            "🔮 **Glyph Timer**": [
                {
                    "name": f"{self.prefix}glyph *(Alias: `g`)*",
                    "value": "Starts a 5-minute cooldown timer for the enemy's glyph.\n**Example:** `{0}glyph`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}cancel-glyph *(Alias: `cg`)*",
                    "value": "Cancels the Glyph cooldown timer.\n**Example:** `{0}cancel-glyph`".format(self.prefix)
                }
            ],
            "🐉 **Tormentor Timer**": [
                {
                    "name": f"{self.prefix}tormentor *(Aliases: `tm`, `torm`, `t`)*",
                    "value": "Logs Tormentor's death and starts the respawn timer.\n**Example:** `{0}tormentor`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}cancel-torm *(Aliases: `ct`, `tormentorcancel`)*",
                    "value": "Cancels the Tormentor respawn timer.\n**Example:** `{0}cancel-torm`".format(self.prefix)
                }
            ],
            "💬 **Mindful Messages**": [
                {
                    "name": f"{self.prefix}enable-mindful *(Aliases: `enable-pma`, `pma`)*",
                    "value": "Enables periodic mindful messages to encourage positive play.\n**Example:** `{0}enable-mindful`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}disable-mindful *(Aliases: `disable-pma`, `no-pma`)*",
                    "value": "Disables the periodic mindful messages.\n**Example:** `{0}disable-mindful`".format(
                        self.prefix)
                }
            ],
            "⚙️ **Custom Events**": [
                {
                    "name": f"{self.prefix}add-event <type> <parameters>",
                    "value": "Adds a custom event.\n**Static:** `{0}add-event static 10:00 \"Siege Creep incoming!\"`\n**Periodic:** `{0}add-event periodic 05:00 02:00 20:00 \"Bounty Runes soon!\"`".format(
                        self.prefix)
                },
                {
                    "name": f"{self.prefix}remove-event <event_id>",
                    "value": "Removes a custom event by its ID.\n**Example:** `{0}remove-event 3`".format(self.prefix)
                },
                {
                    "name": f"{self.prefix}list-events *(Aliases: `ls`, `events`)*",
                    "value": "Lists all custom events.\n**Example:** `{0}list-events`".format(self.prefix)
                },
                {
                    "name": f"{self.prefix}reset-events",
                    "value": "Resets all events to their default values.\n**Example:** `{0}reset-events`".format(
                        self.prefix)
                }
            ],
            "ℹ️ **General**": [
                {
                    "name": f"{self.prefix}bot-help *(Aliases: `dota-help`, `dotahelp`, `pls`, `help`)*",
                    "value": "Shows this help message.\n**Example:** `{0}bot-help`".format(self.prefix)
                }
            ]
        }

        # Add each category and its commands to the embed as separate fields.
        for category, commands_list in categories.items():
            field_value = ""
            for cmd in commands_list:
                field_value += f"**{cmd['name']}**\n{cmd['value']}\n\n"
            embed.add_field(name=category, value=field_value, inline=False)

        # Send the embed to the context channel.
        await ctx.send(embed=embed)
        self.logger.info(f"Help message sent to {ctx.author} in guild ID {ctx.guild.id}")


async def setup(bot: commands.Bot) -> None:
    """
    Function required for loading the Cog.

    Args:
        bot (commands.Bot): The Discord bot instance.
    """
    await bot.add_cog(HelpCog(bot))
