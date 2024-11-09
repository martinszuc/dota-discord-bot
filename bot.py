# bot.py

import discord
from discord.ext import commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import yaml
import ctypes.util
from timer import GameTimer
from roshan import RoshanTimer
from event_manager import EventsManager
from utils import parse_time

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

PREFIX = config.get("prefix", "!")
TIMER_CHANNEL_NAME = config.get("timer_channel", "timer-bot")
VOICE_CHANNEL_NAME = config.get("voice_channel", "DOTA")

# Load Opus library
opus_lib = ctypes.util.find_library('opus')
if opus_lib:
    discord.opus.load_opus(opus_lib)
else:
    logging.warning("Opus library not found. Voice features may not work.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Instantiate timers
events_manager = EventsManager()
game_timers = {}
roshan_timers = {}

# HTTP server to keep bot alive
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, SimpleHandler)
    logger.info("HTTP server started on port 8080")
    httpd.serve_forever()

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    for guild in bot.guilds:
        timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
        if not timer_channel:
            logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in {guild.name}. Please create one.")
        else:
            logger.info(f"Channel '{TIMER_CHANNEL_NAME}' found in {guild.name}.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing required arguments for this command.", tts=True)
        logger.warning(f"Missing arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One or more arguments are invalid.", tts=True)
        logger.warning(f"Bad arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type !bot-help for a list of available commands.", tts=True)
        logger.warning(f"Command not found. Context: {ctx.message.content}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.", tts=True)
        logger.warning(f"Permission denied for user '{ctx.author}'. Command: {ctx.command}")
    else:
        await ctx.send("An error occurred while processing the command.", tts=True)
        logger.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=True)

def is_admin():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

@bot.command(name="start")
async def start(ctx, countdown: int, *args):
    """Start the game timer with a countdown and optionally specify mode and mentions."""
    logger.info(f"Command '!start' invoked by {ctx.author} with countdown={countdown} and args={args}")

    mode = 'regular'
    mentions = None

    # Parse args
    for arg in args:
        if arg.lower() in ['regular', 'turbo']:
            mode = arg.lower()
        elif arg.lower() == 'mention':
            mentions = 'mention'

    # Determine whether to mention players
    mention_users = True if mentions and mentions.lower() == 'mention' else False

    guild_id = ctx.guild.id

    # Check if a timer is already running for this guild
    if guild_id in game_timers and game_timers[guild_id].is_running():
        await ctx.send("A game timer is already running in this server.", tts=True)
        return

    # Find the voice channel
    dota_channel = discord.utils.get(ctx.guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if not dota_channel:
        await ctx.send(f"'{VOICE_CHANNEL_NAME}' voice channel not found. Please create it and try again.", tts=True)
        logger.warning(f"'{VOICE_CHANNEL_NAME}' voice channel not found.")
        return

    # Get the list of members in the voice channel
    players_in_channel = [member for member in dota_channel.members if not member.bot]
    if not players_in_channel:
        await ctx.send(f"No players in the '{VOICE_CHANNEL_NAME}' voice channel.", tts=True)
        logger.warning(f"No players found in the '{VOICE_CHANNEL_NAME}' voice channel.")
        return

    # Prepare player names or mentions
    if mention_users:
        player_names = ', '.join(member.mention for member in players_in_channel)
    else:
        player_names = ', '.join(member.display_name for member in players_in_channel)

    # Send a message in the timer channel and start the timer
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send(f"Starting {mode} game timer with players: {player_names}", tts=True)
        game_timer = GameTimer(guild_id, mode)
        game_timers[guild_id] = game_timer
        roshan_timers[guild_id] = RoshanTimer(game_timer)
        await game_timer.start(timer_channel, countdown, players_in_channel, mention_users)
        logger.info(f"Game timer started by {ctx.author} with countdown={countdown}, mode={mode}, and players={player_names}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
        return

    # Connect to the voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await dota_channel.connect()
    elif voice_client.channel != dota_channel:
        await voice_client.move_to(dota_channel)
    game_timer.voice_client = voice_client

@bot.command(name="stop")
async def stopgame(ctx):
    """Stop the game timer."""
    logger.info(f"Command '!stop' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id in game_timers and game_timers[guild_id].is_running():
        timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
        if timer_channel:
            await game_timers[guild_id].stop()
            await timer_channel.send("Game timer stopped.", tts=True)
            logger.info(f"Game timer stopped by {ctx.author}")
        else:
            await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
            logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
    else:
        await ctx.send("Game timer is not currently running.", tts=True)
        logger.warning(f"{ctx.author} attempted to stop the timer, but it was not running.")

    # Disconnect from the voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
        game_timers[guild_id].voice_client = None

@bot.command(name="pause")
async def pausegame(ctx):
    """Pause the game timer and all events."""
    logger.info(f"Command '!pause' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id in game_timers and game_timers[guild_id].is_running():
        if game_timers[guild_id].is_paused():
            await ctx.send("Game timer is already paused.", tts=True)
            logger.warning(f"{ctx.author} attempted to pause the timer, but it was already paused.")
        else:
            await game_timers[guild_id].pause()
            await ctx.send("Game timer paused.", tts=True)
            logger.info(f"Game timer paused by {ctx.author}")
    else:
        await ctx.send("Game timer is not currently running.", tts=True)
        logger.warning(f"{ctx.author} attempted to pause the timer, but it was not running.")

@bot.command(name="unpause")
async def unpausegame(ctx):
    """Resume the game timer and all events."""
    logger.info(f"Command '!unpause' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id in game_timers and game_timers[guild_id].is_running():
        if not game_timers[guild_id].is_paused():
            await ctx.send("Game timer is not paused.", tts=True)
            logger.warning(f"{ctx.author} attempted to unpause the timer, but it was not paused.")
        else:
            await game_timers[guild_id].unpause()
            await ctx.send("Game timer resumed.", tts=True)
            logger.info(f"Game timer resumed by {ctx.author}")
    else:
        await ctx.send("Game timer is not currently running.", tts=True)
        logger.warning(f"{ctx.author} attempted to unpause the timer, but it was not running.")

@bot.command(name="rosh")
async def rosh(ctx):
    """Log Roshan's death and start the respawn timer."""
    logger.info(f"Command '!rosh' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.", tts=True)
        logger.warning(f"Roshan timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await roshan_timers[guild_id].start(timer_channel)
        logger.info(f"Roshan timer started by {ctx.author}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="glyph")
async def glyph(ctx):
    """Start a 5-minute timer for the enemy's glyph cooldown."""
    logger.info(f"Command '!glyph' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.", tts=True)
        logger.warning(f"Glyph timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send("Enemy glyph used! Starting 5-minute cooldown timer.", tts=True)
        await game_timers[guild_id].start_glyph_timer(timer_channel)
        logger.info(f"Glyph timer started by {ctx.author}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="add-event")
@is_admin()
async def add_event(ctx, event_type: str, *args):
    """Add a custom event. Usage:
    - For static events: !add-event static <time> <message>
    - For periodic events: !add-event periodic <start_time> <interval> <end_time> <message>
    """
    guild_id = ctx.guild.id
    events_manager = EventsManager()
    try:
        if event_type.lower() == 'static':
            time = args[0]
            message = ' '.join(args[1:])
            event_id = events_manager.add_static_event(guild_id, time, message)
            await ctx.send(f"Static event added with ID {event_id}.", tts=True)
        elif event_type.lower() == 'periodic':
            start_time = args[0]
            interval = args[1]
            end_time = args[2]
            message = ' '.join(args[3:])
            event_id = events_manager.add_periodic_event(guild_id, start_time, interval, end_time, message)
            await ctx.send(f"Periodic event added with ID {event_id}.", tts=True)
        else:
            await ctx.send("Invalid event type. Use 'static' or 'periodic'.", tts=True)
    except Exception as e:
        logger.error(f"Error adding event: {e}", exc_info=True)
        await ctx.send(f"Error adding event: {e}", tts=True)
    finally:
        events_manager.close()

@bot.command(name="remove-event")
@is_admin()
async def remove_event(ctx, event_id: int):
    """Remove a custom event by its ID."""
    guild_id = ctx.guild.id
    events_manager = EventsManager()
    try:
        success = events_manager.remove_event(guild_id, event_id)
        if success:
            await ctx.send(f"Event ID {event_id} removed.", tts=True)
        else:
            await ctx.send(f"No event found with ID {event_id}.", tts=True)
    except Exception as e:
        logger.error(f"Error removing event: {e}", exc_info=True)
        await ctx.send(f"Error removing event: {e}", tts=True)
    finally:
        events_manager.close()

@bot.command(name="list-events")
async def list_events(ctx):
    """List all custom events."""
    guild_id = ctx.guild.id
    events_manager = EventsManager()
    try:
        events = events_manager.list_events(guild_id)
        if events:
            event_list = ""
            for event in events:
                if event.event_type == 'static':
                    event_list += f"ID: {event.id}, Type: Static, Time: {event.time}, Message: {event.message}\n"
                elif event.event_type == 'periodic':
                    event_list += f"ID: {event.id}, Type: Periodic, Start: {event.start_time}, Interval: {event.interval}, End: {event.end_time}, Message: {event.message}\n"
            embed = discord.Embed(title="Custom Events", description=event_list, color=0x00ff00)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No custom events found.", tts=True)
    except Exception as e:
        logger.error(f"Error listing events: {e}", exc_info=True)
        await ctx.send(f"Error listing events: {e}", tts=True)
    finally:
        events_manager.close()

@bot.command(name="bot-help")
async def bot_help(ctx):
    """Show available commands with examples."""
    logger.info(f"Command '!bot-help' invoked by {ctx.author}")
    help_message = """
**Dota Timer Bot - Help**

- `!start <countdown> [mode] [mention]`
  - Starts the game timer with a countdown. Add 'mention' to mention players.
  - **mode** can be 'regular' or 'turbo'. Defaults to 'regular'.
  - **Example:** `!start 3` or `!start 3 turbo mention`

- `!stop`
  - Stops the current game timer.
  - **Example:** `!stop`

- `!pause`
  - Pauses the game timer and all events.
  - **Example:** `!pause`

- `!unpause`
  - Resumes the game timer and all events.
  - **Example:** `!unpause`

- `!rosh`
  - Logs Roshan's death and starts an 8-minute respawn timer.
  - **Example:** `!rosh`

- `!glyph`
  - Starts a 5-minute cooldown timer for the enemy's glyph.
  - **Example:** `!glyph`

- `!add-event <type> <parameters>`
  - Adds a custom event.
  - **Static Event Example:** `!add-event static 10:00 "Siege Creep incoming!"`
  - **Periodic Event Example:** `!add-event periodic 05:00 02:00 20:00 "Bounty Runes soon!"`

- `!remove-event <event_id>`
  - Removes a custom event by its ID.
  - **Example:** `!remove-event 3`

- `!list-events`
  - Lists all custom events.
  - **Example:** `!list-events`

- `!bot-help`
  - Shows this help message.
  - **Example:** `!bot-help`
    """
    await ctx.send(help_message)
    logger.info(f"Help message sent to {ctx.author}")

# Start the HTTP server in a separate thread
threading.Thread(target=run_server, daemon=True).start()
logger.info("HTTP server thread started.")

# Run the bot
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    logger.error("Bot token not found. Please set the 'DISCORD_BOT_TOKEN' environment variable.")
