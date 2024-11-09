# bot.py

import discord
from discord.ext import commands, tasks
import os
import asyncio
from aiohttp import web
import logging
import yaml
import ctypes.util
import signal

from timer import GameTimer
from roshan import RoshanTimer
from event_manager import EventsManager
from utils import parse_time

# Load configuration from config.yaml
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

PREFIX = config.get("prefix", "!")
TIMER_CHANNEL_NAME = config.get("timer_channel", "timer-bot")
VOICE_CHANNEL_NAME = config.get("voice_channel", "DOTA")
HTTP_SERVER_PORT = config.get("http_server_port", 8080)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DotaDiscordBot')

# Load Opus library for voice support
opus_lib = ctypes.util.find_library('opus')
if opus_lib:
    discord.opus.load_opus(opus_lib)
    logger.info("Opus library loaded successfully.")
else:
    logger.warning("Opus library not found. Voice features may not work.")

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# Initialize the bot
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Instantiate EventsManager
events_manager = EventsManager()

# Data structures to keep track of timers and Roshan timers per guild
game_timers = {}
roshan_timers = {}

# HTTP server setup using aiohttp
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', HTTP_SERVER_PORT)
    await site.start()
    logger.info(f"HTTP server started on port {HTTP_SERVER_PORT}")

# Event: Bot is ready
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('------')
    for guild in bot.guilds:
        timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
        if not timer_channel:
            logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{guild.name}'. Please create it.")
        else:
            logger.info(f"Channel '{TIMER_CHANNEL_NAME}' found in guild '{guild.name}'.")

# Event: Bot joins a new guild
@bot.event
async def on_guild_join(guild):
    """Initialize events for a guild only if they don't already exist."""
    logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")

    # Check if this guild already has events
    if not events_manager.guild_has_events(guild.id):
        # Populate initial events for this guild only if they don't exist
        events_manager.initialize_guild_events(guild.id)
        logger.info(f"Initialized events for guild '{guild.name}' (ID: {guild.id}).")
    else:
        logger.info(f"Guild '{guild.name}' (ID: {guild.id}) already has events, skipping initialization.")

    # Send a welcome message to the system channel or the first text channel if available
    channel = guild.system_channel or next(
        (chan for chan in guild.text_channels if chan.permissions_for(guild.me).send_messages), None)
    if channel:
        await channel.send("Dota Timer Bot has been added to this server! Type `!bot-help` to get started.")

# Event: Command errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing required arguments for this command.", tts=True)
        logger.warning(f"Missing arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One or more arguments are invalid.", tts=True)
        logger.warning(f"Bad arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Type {PREFIX}bot-help for a list of available commands.", tts=True)
        logger.warning(f"Command not found. Context: {ctx.message.content}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.", tts=True)
        logger.warning(f"Permission denied for user '{ctx.author}'. Command: {ctx.command}")
    else:
        await ctx.send("An unexpected error occurred.", tts=True)
        logger.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=True)

# Check: Admin permissions
def is_admin():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# Command: Start game timer
@bot.command(name="start")
async def start_game(ctx, countdown: int, *args):
    """Start the game timer with a countdown and optionally specify mode and mentions."""
    logger.info(f"Command '!start' invoked by {ctx.author} with countdown={countdown} and args={args}")

    mode = 'regular'
    mention_users = False

    # Parse arguments
    for arg in args:
        if arg.lower() in ['regular', 'turbo']:
            mode = arg.lower()
        elif arg.lower() == 'mention':
            mention_users = True

    guild_id = ctx.guild.id

    # Check if a timer is already running for this guild
    if guild_id in game_timers and game_timers[guild_id].is_running():
        await ctx.send("A game timer is already running in this server.", tts=True)
        return

    # Find the voice channel
    dota_voice_channel = discord.utils.get(ctx.guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if not dota_voice_channel:
        await ctx.send(f"'{VOICE_CHANNEL_NAME}' voice channel not found. Please create it and try again.", tts=True)
        logger.warning(f"'{VOICE_CHANNEL_NAME}' voice channel not found.")
        return

    # Get the list of members in the voice channel
    players_in_channel = [member for member in dota_voice_channel.members if not member.bot]
    if not players_in_channel:
        await ctx.send(f"No players in the '{VOICE_CHANNEL_NAME}' voice channel.", tts=True)
        logger.warning(f"No players found in the '{VOICE_CHANNEL_NAME}' voice channel.")
        return

    # Prepare player names or mentions
    if mention_users:
        player_names = ', '.join(member.mention for member in players_in_channel)
    else:
        player_names = ', '.join(member.display_name for member in players_in_channel)

    # Get the timer text channel
    timer_text_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if not timer_text_channel:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
        return

    # Announce the start of the game timer
    await timer_text_channel.send(f"Starting {mode} game timer with players: {player_names}", tts=True)

    # Initialize and start the GameTimer
    game_timer = GameTimer(guild_id, mode)
    game_timers[guild_id] = game_timer
    roshan_timer = RoshanTimer(game_timer)
    roshan_timers[guild_id] = roshan_timer

    # Connect to the voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await dota_voice_channel.connect()
    elif voice_client.channel != dota_voice_channel:
        await voice_client.move_to(dota_voice_channel)
    game_timer.voice_client = voice_client

    # Start the game timer
    await game_timer.start(timer_text_channel, countdown, players_in_channel, mention_users)
    logger.info(f"Game timer started by {ctx.author} with countdown={countdown}, mode={mode}, and players={player_names}")

# Command: Stop game timer
@bot.command(name="stop")
async def stop_game(ctx):
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
        if guild_id in game_timers:
            game_timers[guild_id].voice_client = None
    else:
        logger.warning("Voice client was not connected.")

# Command: Pause game timer
@bot.command(name="pause")
async def pause_game(ctx):
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

# Command: Unpause game timer
@bot.command(name="unpause")
async def unpause_game(ctx):
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

# Command: Roshan timer
@bot.command(name="rosh")
async def rosh_timer(ctx):
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

# Command: Glyph cooldown timer
@bot.command(name="glyph")
async def glyph_timer(ctx):
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

# Command: Add custom event
@bot.command(name="add-event")
@is_admin()
async def add_event_command(ctx, event_type: str, *args):
    """
    Add a custom event.
    Usage:
    - For static events: !add-event static <time> <message>
    - For periodic events: !add-event periodic <start_time> <interval> <end_time> <message>
    """
    logger.info(f"Command '!add-event' invoked by {ctx.author} with event_type={event_type} and args={args}")
    guild_id = ctx.guild.id
    try:
        if event_type.lower() == 'static':
            if len(args) < 2:
                await ctx.send("Insufficient arguments for static event. Usage: `!add-event static <MM:SS> <message>`", tts=True)
                return
            time_str = args[0]
            message = ' '.join(args[1:])
            time_seconds = parse_time(time_str)
            event_id = events_manager.add_static_event(guild_id, time_seconds, message)
            await ctx.send(f"Static event added with ID {event_id}.", tts=True)
            logger.info(f"Static event added with ID {event_id} by {ctx.author}")
        elif event_type.lower() == 'periodic':
            if len(args) < 4:
                await ctx.send("Insufficient arguments for periodic event. Usage: `!add-event periodic <MM:SS> <MM:SS> <MM:SS> <message>`", tts=True)
                return
            start_time_str = args[0]
            interval_str = args[1]
            end_time_str = args[2]
            message = ' '.join(args[3:])
            start_time = parse_time(start_time_str)
            interval = parse_time(interval_str)
            end_time = parse_time(end_time_str)
            event_id = events_manager.add_periodic_event(guild_id, start_time, interval, end_time, message)
            await ctx.send(f"Periodic event added with ID {event_id}.", tts=True)
            logger.info(f"Periodic event added with ID {event_id} by {ctx.author}")
        else:
            await ctx.send("Invalid event type. Use 'static' or 'periodic'.", tts=True)
            logger.warning(f"Invalid event type '{event_type}' used by {ctx.author}")
    except ValueError:
        await ctx.send("Invalid time format. Please use MM:SS format.", tts=True)
        logger.error(f"Invalid time format used by {ctx.author} with args={args}")
    except Exception as e:
        await ctx.send(f"Error adding event: {e}", tts=True)
        logger.error(f"Error adding event by {ctx.author}: {e}", exc_info=True)

# Command: Remove custom event
@bot.command(name="remove-event")
@is_admin()
async def remove_event_command(ctx, event_id: int):
    """Remove a custom event by its ID."""
    logger.info(f"Command '!remove-event' invoked by {ctx.author} with event_id={event_id}")
    guild_id = ctx.guild.id
    try:
        success = events_manager.remove_event(guild_id, event_id)
        if success:
            await ctx.send(f"Event ID {event_id} removed.", tts=True)
            logger.info(f"Event ID {event_id} removed by {ctx.author}")
        else:
            await ctx.send(f"No event found with ID {event_id}.", tts=True)
            logger.warning(f"Event ID {event_id} not found for removal by {ctx.author}")
    except Exception as e:
        await ctx.send(f"Error removing event: {e}", tts=True)
        logger.error(f"Error removing event ID {event_id} by {ctx.author}: {e}", exc_info=True)

# Command: List custom events
@bot.command(name="list-events")
async def list_events_command(ctx):
    """List all custom events."""
    logger.info(f"Command '!list-events' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    static_events = events_manager.get_static_events(guild_id)
    periodic_events = events_manager.get_periodic_events(guild_id)

    if not static_events and not periodic_events:
        await ctx.send("No custom events found.")
    else:
        await ctx.send(f"Static Events: {static_events}\nPeriodic Events: {periodic_events}")

# (Other command implementations here...)

# Graceful shutdown handling
async def shutdown():
    logger.info("Shutting down bot...")
    # Stop all game timers
    for guild_id, timer in game_timers.items():
        if timer.is_running():
            await timer.stop()
    # Close the EventsManager session
    events_manager.close()
    # Disconnect all voice clients
    for voice_client in bot.voice_clients:
        await voice_client.disconnect()
    # Close the bot
    await bot.close()
    logger.info("Bot has been shut down.")

# Handle termination signals for graceful shutdown
def handle_signal(sig):
    logger.info(f"Received exit signal {sig.name}...")
    asyncio.create_task(shutdown())

# Register signal handlers
signal.signal(signal.SIGINT, lambda s, f: handle_signal(signal.Signals.SIGINT))
signal.signal(signal.SIGTERM, lambda s, f: handle_signal(signal.Signals.SIGTERM))

# Main entry point
async def main():
    # Start the HTTP server
    await start_http_server()
    # Run the bot
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        logger.error("Bot token not found. Please set the 'DISCORD_BOT_TOKEN' environment variable.")
        return
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
