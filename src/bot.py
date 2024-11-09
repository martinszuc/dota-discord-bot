# src/bot.py

import asyncio
import ctypes.util
import os
import signal

import discord
from discord.ext import commands

from src.managers.event_manager import EventsManager
from src.timer import GameTimer
from src.utils.config import PREFIX, TIMER_CHANNEL_NAME, VOICE_CHANNEL_NAME, logger
from src.utils.utils import min_to_sec

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

# Initialize the bot with no default help command
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Instantiate EventsManager
events_manager = EventsManager()

# Data structures to keep track of game and child timers per guild
game_timers = {}

WEBHOOK_ID = os.getenv('WEBHOOK_ID')


@bot.event
async def on_message(message):
    # Log received message details for troubleshooting
    logger.info(
        f"Received message in channel {message.channel} from {message.author} with ID {message.webhook_id}: {message.content}")

    # Ignore messages from the bot itself to avoid command loops
    if message.author == bot.user:
        logger.info("Ignoring message from the bot itself.")
        return

    # Check if message is from the specified webhook and contains a command
    if str(message.webhook_id) == WEBHOOK_ID and message.content.startswith(PREFIX):
        logger.info("Message is from the webhook and matches the command prefix.")

        # Mock the author to have all permissions to bypass potential permission checks
        message.author = type('User', (object,), {'guild_permissions': discord.Permissions.all()})()

        # Attempt to process the message as a command
        ctx = await bot.get_context(message)
        logger.info(f"Context created for webhook message: {ctx.command}, valid: {ctx.valid}")

        if ctx.valid:
            try:
                await bot.invoke(ctx)
                logger.info("Webhook command invoked successfully.")
            except Exception as e:
                logger.error(f"Error while invoking command from webhook: {e}", exc_info=True)
        else:
            logger.warning("Webhook message did not create a valid command context.")

        return

    # Process regular user commands
    if message.content.startswith(PREFIX):
        logger.info("Processing user command.")
        await bot.process_commands(message)

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
        await channel.send(f"Dota Timer Bot has been added to this server! Type `{PREFIX}bot-help` to get started.")

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
        await ctx.send(f"Command not found. Type `{PREFIX}bot-help` for a list of available commands.", tts=True)
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

# Load all cogs in the 'cogs' directory
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            extension = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(extension)
                logger.info(f"Loaded cog: {extension}")
            except Exception as e:
                logger.error(f"Failed to load cog {extension}: {e}", exc_info=True)

# Command: Start game timer
@bot.command(name="start")
async def start_game(ctx, countdown: int, *args):
    logger.info(f"Executing 'start' command with countdown={countdown} and args={args}")

    mode = 'regular'
    for arg in args:
        if arg.lower() in ['regular', 'turbo']:
            mode = arg.lower()

    guild_id = ctx.guild.id

    # Check if a timer is already running for this guild
    if guild_id in game_timers and game_timers[guild_id].is_running():
        await ctx.send("A game timer is already running in this server.", tts=True)
        logger.info("A game timer is already running; start command ignored.")
        return

    # Find the voice channel
    dota_voice_channel = discord.utils.get(ctx.guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if not dota_voice_channel:
        await ctx.send(f"'{VOICE_CHANNEL_NAME}' voice channel not found. Please create it and try again.", tts=True)
        logger.warning(f"'{VOICE_CHANNEL_NAME}' voice channel not found.")
        return

    # Get the timer text channel
    timer_text_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if not timer_text_channel:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
        return

    # Announce the start of the game timer
    await timer_text_channel.send(f"Starting {mode} game timer.")
    logger.info(f"Starting game timer with mode={mode}.")

    # Initialize and start the GameTimer
    game_timer = GameTimer(guild_id, mode)
    game_timer.channel = timer_text_channel
    game_timers[guild_id] = game_timer

    # Connect to the voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await dota_voice_channel.connect()
    elif voice_client.channel != dota_voice_channel:
        await voice_client.move_to(dota_voice_channel)
    game_timer.voice_client = voice_client

    # Start the game timer
    await game_timer.start(timer_text_channel, countdown)
    logger.info(f"Game timer successfully started by {ctx.author} with countdown={countdown} and mode={mode}.")

# Command: Stop game timer
@bot.command(name="stop")
async def stop_game(ctx):
    """Stop the game timer and all associated timers (Roshan, Glyph, Tormentor)."""
    logger.info(f"Command '!stop' invoked by {ctx.author}")
    guild_id = ctx.guild.id

    if guild_id in game_timers and game_timers[guild_id].is_running():
        timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
        if timer_channel:
            # Stop the game timer
            await game_timers[guild_id].stop()
            await timer_channel.send("Game timer stopped.")
            logger.info(f"Game timer stopped by {ctx.author}")

            # Remove the timer from the dictionary
            del game_timers[guild_id]
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
@bot.command(name="unpause", aliases=['unp', 'up'])
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
@bot.command(name="rosh", aliases=['rs', 'rsdead'])
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
        roshan_timer = game_timers[guild_id].roshan_timer
        if not roshan_timer.is_running:
            await roshan_timer.start(timer_channel)
            await timer_channel.send("Roshan timer started.")
            logger.info(f"Roshan timer started by {ctx.author}")
        else:
            await ctx.send("Roshan timer is already running.", tts=True)
            logger.warning(f"{ctx.author} attempted to start Roshan timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

# Command: Cancel Roshan timer
@bot.command(name='cancel-rosh', aliases=['rsalive', 'rsback', 'rsb'])
async def cancel_rosh_command(ctx):
    """Cancel the Roshan respawn timer."""
    logger.info(f"Command '!cancel-rosh' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        roshan_timer = game_timers[guild_id].roshan_timer
        if roshan_timer.is_running:
            await roshan_timer.stop()
            await timer_channel.send("Roshan timer has been cancelled.")
            logger.info(f"Roshan timer cancelled by {ctx.author}")
        else:
            await ctx.send("No active Roshan timer to cancel.", tts=True)
            logger.warning(f"No active Roshan timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.", tts=True)
        logger.warning(f"{ctx.author} attempted to cancel Roshan timer, but game timer is not active.")

# Command: Glyph cooldown timer
@bot.command(name="glyph", aliases=['g'])
async def glyph_timer_command(ctx):
    """Start the Glyph cooldown timer."""
    logger.info(f"Command '!glyph' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.", tts=True)
        logger.warning(f"Glyph timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        glyph_timer = game_timers[guild_id].glyph_timer
        if not glyph_timer.is_running:
            await glyph_timer.start(timer_channel)
            await timer_channel.send("Glyph timer started.")
            logger.info(f"Glyph timer started by {ctx.author}")
        else:
            await ctx.send("Glyph timer is already running.", tts=True)
            logger.warning(f"{ctx.author} attempted to start Glyph timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

# Command: Cancel Glyph timer
@bot.command(name="cancel-glyph", aliases=['cg'])
async def cancel_glyph_command(ctx):
    """Cancel the Glyph cooldown timer."""
    logger.info(f"Command '!cancel-glyph' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        glyph_timer = game_timers[guild_id].glyph_timer
        if glyph_timer.is_running:
            await glyph_timer.stop()
            await timer_channel.send("Glyph timer has been cancelled.")
            logger.info(f"Glyph timer cancelled by {ctx.author}")
        else:
            await ctx.send("No active Glyph timer to cancel.", tts=True)
            logger.warning(f"No active Glyph timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.", tts=True)
        logger.warning(f"{ctx.author} attempted to cancel Glyph timer, but game timer is not active.")

# Command: Tormentor timer
@bot.command(name="tormentor", aliases=['tm', 'torm', 't'])
async def tormentor_timer_command(ctx):
    """Log Tormentor's death and start the respawn timer."""
    logger.info(f"Command '!tormentor' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.", tts=True)
        logger.warning(f"Tormentor timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        tormentor_timer = game_timers[guild_id].tormentor_timer
        if not tormentor_timer.is_running:
            await tormentor_timer.start(timer_channel)
            await timer_channel.send("Tormentor timer started.")
            logger.info(f"Tormentor timer started by {ctx.author}")
        else:
            await ctx.send("Tormentor timer is already running.", tts=True)
            logger.warning(f"{ctx.author} attempted to start Tormentor timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.", tts=True)
        logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

# Command: Cancel Tormentor timer
@bot.command(name="cancel-torm", aliases=['ct', 'tormentorcancel'])
async def cancel_tormentor_command(ctx):
    """Cancel the Tormentor respawn timer."""
    logger.info(f"Command '!cancel-torm' invoked by {ctx.author}")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        tormentor_timer = game_timers[guild_id].tormentor_timer
        if tormentor_timer.is_running:
            await tormentor_timer.stop()
            await timer_channel.send("Tormentor timer has been cancelled.")
            logger.info(f"Tormentor timer cancelled by {ctx.author}")
        else:
            await ctx.send("No active Tormentor timer to cancel.", tts=True)
            logger.warning(f"No active Tormentor timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.", tts=True)
        logger.warning(f"{ctx.author} attempted to cancel Tormentor timer, but game timer is not active.")

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
                await ctx.send("Insufficient arguments for static event. Usage: `!add-event static <MM:SS> <message>`", tts=True)
                return
            time_str = args[0]
            message = ' '.join(args[1:])
            time_seconds = min_to_sec(time_str)
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
            start_time = min_to_sec(start_time_str)
            interval = min_to_sec(interval_str)
            end_time = min_to_sec(end_time_str)
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
@bot.command(name="list-events", aliases=['ls', 'events'])
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

# Graceful shutdown handling
async def shutdown():
    logger.info("Initiating bot shutdown...")

    # Stop all game timers quickly
    for guild_id, timer in game_timers.items():
        if timer.is_running():
            try:
                await asyncio.wait_for(timer.stop(), timeout=2)  # Set a shorter timeout for each stop call
            except asyncio.TimeoutError:
                logger.warning(f"Timer for guild {guild_id} took too long to stop; forced stop.")

    # Disconnect all voice clients with a timeout
    disconnect_tasks = [vc.disconnect() for vc in bot.voice_clients]
    try:
        await asyncio.wait_for(asyncio.gather(*disconnect_tasks), timeout=5)  # Disconnect all within 5 seconds
    except asyncio.TimeoutError:
        logger.warning("Some voice clients did not disconnect within the timeout.")

    # Close the EventsManager session quickly
    events_manager.close()

    await bot.close()  # Properly close the bot
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
    async with bot:
        await load_cogs()
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
