# bot.py
import asyncio
import ctypes.util
import logging
import os
import signal

import discord
import yaml
from discord.ext import commands

from .event_manager import EventsManager
from .roshan import RoshanTimer
from .timer import GameTimer
from .utils import parse_time

# Load configuration from config.yaml
with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

PREFIX = config.get("prefix", "!")
TIMER_CHANNEL_NAME = config.get("timer_channel", "timer-bot")
VOICE_CHANNEL_NAME = config.get("voice_channel", "DOTA")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/bot.log"),
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
    logger.info(f"Bot joined new guild: {guild.name} (ID: {guild.id})")

    # Check if this guild already has events
    if not events_manager.guild_has_events(guild.id):
        events_manager.populate_events_for_guild(guild.id)
        logger.info(f"Populated events for new guild: {guild.name}")
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
    await timer_text_channel.send(f"Starting {mode} game timer with players: {player_names}")

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
    logger.info(
        f"Game timer started by {ctx.author} with countdown={countdown}, mode={mode}, and players={player_names}")


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
            await timer_channel.send("Game timer stopped.")
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
@bot.command(name="pause", aliases=['p'])
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
@bot.command(name="unpause", aliases=['unp'])
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
@bot.command(name="rosh", aliases=['rs', 'rsdead', 'rs-dead', 'rsdied', 'rs-died'])
async def rosh_timer_command(ctx):
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
@bot.command(name="glyph", aliases=['g'])
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
        await timer_channel.send("Enemy glyph used! Starting 5-minute cooldown timer.")
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
    - For static events: !add-event static <MM:SS> <message>
    - For periodic events: !add-event periodic <MM:SS> <MM:SS> <MM:SS> <message>
    """
    logger.info(f"Command '!add-event' invoked by {ctx.author} with event_type={event_type} and args={args}")
    guild_id = ctx.guild.id
    try:
        if event_type.lower() == 'static':
            if len(args) < 2:
                await ctx.send("Insufficient arguments for static event. Usage: `!add-event static <MM:SS> <message>`",
                               tts=True)
                return
            time_str = args[0]
            message = ' '.join(args[1:])
            time_seconds = parse_time(time_str)
            event_id = events_manager.add_static_event(guild_id, time_seconds, message)
            await ctx.send(f"Static event added with ID {event_id}.", tts=True)
            logger.info(f"Static event added with ID {event_id} by {ctx.author}")
        elif event_type.lower() == 'periodic':
            if len(args) < 4:
                await ctx.send(
                    "Insufficient arguments for periodic event. Usage: `!add-event periodic <MM:SS> <MM:SS> <MM:SS> <message>`",
                    tts=True)
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
@bot.command(name="list-events", aliases=[('ls', 'events')])
async def list_events_command(ctx):
    """List all custom events for the current guild."""
    logger.info(f"Command '!list-events' invoked by {ctx.author}")
    guild_id = ctx.guild.id

    # Retrieve events specific to this guild
    static_events = events_manager.get_static_events(guild_id)
    periodic_events = events_manager.get_periodic_events(guild_id)

    # Check if any events exist
    if not static_events and not periodic_events:
        await ctx.send("No custom events found for this guild.")
        return

    # Create an embed message for better readability
    embed = discord.Embed(title=f"Events for Guild: {ctx.guild.name}", color=0x00ff00)

    # Add static events to the embed
    if static_events:
        embed.add_field(name="**Static Events:**", value="", inline=False)
        for event_id, event_data in static_events.items():
            time_formatted = f"{event_data['time'] // 60:02}:{event_data['time'] % 60:02}"
            embed.add_field(
                name=f"ID {event_id} (Static)",
                value=f"Time: {time_formatted}\nMessage: {event_data['message']}",
                inline=False
            )

    # Add periodic events to the embed
    if periodic_events:
        embed.add_field(name="**Periodic Events:**", value="", inline=False)
        for event_id, event_data in periodic_events.items():
            start_formatted = f"{event_data['start_time'] // 60:02}:{event_data['start_time'] % 60:02}"
            interval_formatted = f"{event_data['interval'] // 60:02}:{event_data['interval'] % 60:02}"
            end_formatted = f"{event_data['end_time'] // 60:02}:{event_data['end_time'] % 60:02}"
            embed.add_field(
                name=f"ID {event_id} (Periodic)",
                value=f"Start Time: {start_formatted}\nInterval: {interval_formatted}\nEnd Time: {end_formatted}\nMessage: {event_data['message']}",
                inline=False
            )

    # Send the embed message with the events list
    await ctx.send(embed=embed)
    logger.info(f"Events listed for guild '{ctx.guild.name}' (ID: {guild_id})")


@bot.command(name='cancel-rosh', aliases=['rsalive', 'rsback', 'rs-cancel', 'rs-back', 'rs-alive', 'rsb'])
async def cancel_rosh_command(ctx):
    """Cancel the Roshan respawn timer."""
    logger.info(f"Command '!cancel-rosh' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.", tts=True)
        logger.warning(f"Roshan timer cancel attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await game_timers[guild_id].roshan_timer.cancel()
        await timer_channel.send("Roshan timer has been cancelled.")
        logger.info(f"Roshan timer cancelled by {ctx.author}")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

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
    # Run the bot
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("Bot token not found. Please set the 'DISCORD_BOT_TOKEN' environment variable.")
        return
    await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
