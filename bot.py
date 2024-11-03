import discord
from discord.ext import commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from timer import GameTimer
from roshan import RoshanTimer
from events import STATIC_EVENTS, PERIODIC_EVENTS
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Initialize intents and bot, disabling the default help command
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable members intent
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Instantiate timers
game_timer = GameTimer()
roshan_timer = RoshanTimer()

# Constants
TIMER_CHANNEL_NAME = "timer-bot"
VOICE_CHANNEL_NAME = "DOTA"  # Name of the voice channel to monitor

# HTTP server to keep bot alive
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, SimpleHandler)
    logging.info("HTTP server started on port 8080")
    httpd.serve_forever()

# Event handlers
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')
    for guild in bot.guilds:
        timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
        if not timer_channel:
            logging.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in {guild.name}. Please create one.")
        else:
            logging.info(f"Channel '{TIMER_CHANNEL_NAME}' found in {guild.name}.")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing required arguments for this command.")
        logging.warning(f"Missing arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One or more arguments are invalid.")
        logging.warning(f"Bad arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type `!bot-help` for a list of available commands.")
        logging.warning(f"Command not found. Context: {ctx.message.content}")
    else:
        await ctx.send("An error occurred while processing the command.")
        logging.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=True)

# Commands
@bot.command(name="start")
async def start(ctx, countdown: int, mentions: str = None):
    """Start the game timer with a countdown and optionally mention players in the 'DOTA' voice channel."""
    logging.info(f"Command '!start' invoked by {ctx.author} with countdown={countdown} and mentions={mentions}")

    # Determine whether to mention players
    mention_users = True if mentions and mentions.lower() == 'mention' else False

    # Find the "DOTA" voice channel
    dota_channel = discord.utils.get(ctx.guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if not dota_channel:
        await ctx.send(f"'{VOICE_CHANNEL_NAME}' voice channel not found. Please create it and try again.")
        logging.warning(f"'{VOICE_CHANNEL_NAME}' voice channel not found.")
        return

    # Get the list of members in the "DOTA" voice channel
    players_in_channel = [member for member in dota_channel.members if not member.bot]
    if not players_in_channel:
        await ctx.send(f"No players in the '{VOICE_CHANNEL_NAME}' voice channel.")
        logging.warning(f"No players found in the '{VOICE_CHANNEL_NAME}' voice channel.")
        return

    # Prepare player names or mentions
    if mention_users:
        player_names = ', '.join(member.mention for member in players_in_channel)
    else:
        player_names = ', '.join(member.display_name for member in players_in_channel)

    # Send a message in the timer channel and start the timer
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send(f"Starting game timer with players: {player_names}", tts=True)
        await game_timer.start(timer_channel, countdown, players_in_channel, mention_users)
        logging.info(f"Game timer started by {ctx.author} with countdown={countdown} and players={player_names}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="stop")
async def stopgame(ctx):
    """Stop the game timer."""
    logging.info(f"Command '!stop' invoked by {ctx.author}")
    if game_timer.is_running():
        timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
        if timer_channel:
            await game_timer.stop()
            await timer_channel.send("Game timer stopped.", tts=True)
            logging.info(f"Game timer stopped by {ctx.author}")
        else:
            await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
            logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
    else:
        await ctx.send("Game timer is not currently running.")
        logging.warning(f"{ctx.author} attempted to stop the timer, but it was not running.")

@bot.command(name="rosh")
async def rosh(ctx):
    """Log Roshan's death and start the respawn timer."""
    logging.info(f"Command '!rosh' invoked by {ctx.author}")
    if not game_timer.is_running():
        await ctx.send("Game is not active.")
        logging.warning(f"Roshan timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await roshan_timer.start(timer_channel)
        logging.info(f"Roshan timer started by {ctx.author}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="glyph")
async def glyph(ctx):
    """Start a 5-minute timer for the enemy's glyph cooldown."""
    logging.info(f"Command '!glyph' invoked by {ctx.author}")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send("Enemy glyph used! Starting 5-minute cooldown timer.", tts=True)
        await game_timer.start_glyph_timer(timer_channel)
        logging.info(f"Glyph timer started by {ctx.author}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

# You can adjust or remove the following commands if you're not using target groups anymore.

@bot.command(name="bot-help")
async def bot_help(ctx):
    """Show available commands with examples."""
    logging.info(f"Command '!bot-help' invoked by {ctx.author}")
    help_message = """
**Dota Timer Bot - Help**

- `!start <countdown> [mention]`
  - Starts the game timer with a countdown. Add 'mention' to mention players.
  - **Example:** `!start 3` or `!start 3 mention`

- `!stop`
  - Stops the current game timer.
  - **Example:** `!stop`

- `!rosh`
  - Logs Roshan's death and starts an 8-minute respawn timer.
  - **Example:** `!rosh`

- `!glyph`
  - Starts a 5-minute cooldown timer for the enemy's glyph.
  - **Example:** `!glyph`

- `!bot-help`
  - Shows this help message.
  - **Example:** `!bot-help`
    """
    await ctx.send(help_message)
    logging.info(f"Help message sent to {ctx.author}")

# Start the HTTP server in a separate thread
threading.Thread(target=run_server, daemon=True).start()
logging.info("HTTP server thread started.")

# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
