# cogs/help_cog.py

import logging

from discord.ext import commands

from src.utils.config import PREFIX


class HelpCog(commands.Cog):
    """A Cog for handling the help command."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('DotaDiscordBot')
        self.prefix = PREFIX

    @commands.command(name="bot-help", aliases=['dota-help', 'dotahelp', 'pls', 'help'])
    async def send_help(self, ctx):
        """Show available commands with examples."""
        self.logger.info(f"Command '!bot-help' invoked by {ctx.author}")
        help_message = f"""
**Dota Timer Bot - Help**

- `{self.prefix}start <countdown> [mode] [mention]`
  - Starts the game timer with a countdown. Add 'mention' to mention players.
  - **mode** can be 'regular' or 'turbo'. Defaults to 'regular'.
  - **Example:** `{self.prefix}start 180` or `{self.prefix}start 180 turbo mention`

- `{self.prefix}stop`
  - Stops the current game timer.
  - **Example:** `{self.prefix}stop`

- `{self.prefix}pause` *(Alias: `p`)*
  - Pauses the game timer and all events.
  - **Example:** `{self.prefix}pause`

- `{self.prefix}unpause` *(Alias: `unp`)*
  - Resumes the game timer and all events.
  - **Example:** `{self.prefix}unpause`

- `{self.prefix}rosh` *(Aliases: `rs`, `rsdead`, `rs-dead`, `rsdied`, `rs-died`)*
  - Logs Roshan's death and starts the respawn timer.
  - **Example:** `{self.prefix}rosh`

- `{self.prefix}cancel-rosh` *(Aliases: `rsalive`, `rsback`, `rs-cancel`, `rs-back`, `rs-alive`, `rsb`)*
  - Cancels the Roshan respawn timer if it's active.
  - **Example:** `{self.prefix}cancel-rosh`

- `{self.prefix}glyph` *(Alias: `g`)*
  - Starts a 5-minute cooldown timer for the enemy's glyph.
  - **Example:** `{self.prefix}glyph`
  
- `{self.prefix}cancel-glyph` *(Aliases: `cg`)*
  - Cancels the Glyph cooldown timer.
  - **Example:** `{self.prefix}cancel-glyph`
  
- `{self.prefix}tormentor` *(Aliases: `tm`, `torm`)*
  - Logs Tormentor's death and starts the respawn timer.
  - **Example:** `{self.prefix}tormentor`

- `{self.prefix}add-event <type> <parameters>`
  - Adds a custom event.
  - **Static Event Example:** `{self.prefix}add-event static 10:00 "Siege Creep incoming!"`
  - **Periodic Event Example:** `{self.prefix}add-event periodic 05:00 02:00 20:00 "Bounty Runes soon!"`

- `{self.prefix}remove-event <event_id>`
  - Removes a custom event by its ID.
  - **Example:** `{self.prefix}remove-event 3`

- `{self.prefix}list-events` *(Aliases: `ls`, `events`)*
  - Lists all custom events.
  - **Example:** `{self.prefix}list-events`

- `{self.prefix}bot-help` *(Aliases: `dota-help`, `dotahelp`, `pls`, `help`)*
  - Shows this help message.
  - **Example:** `{self.prefix}bot-help`
        """
        await ctx.send(help_message, tts=True)
        self.logger.info(f"Help message sent to {ctx.author}")

async def setup(bot):
    """Function required for loading the Cog."""
    await bot.add_cog(HelpCog(bot))
