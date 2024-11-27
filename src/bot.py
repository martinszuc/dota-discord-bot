# src/bot.py

import asyncio
import ctypes.util
import os
import signal
import re
import logging

import discord
from discord.ext import commands

from src.managers.event_manager import EventsManager
from src.timer import GameTimer
from src.utils.config import PREFIX, TIMER_CHANNEL_NAME, VOICE_CHANNEL_NAME, logger, COGS_DIRECTORY
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
logger.debug("EventsManager instantiated.")

# Data structures to keep track of game and child timers per guild
game_timers = {}
timer_locks = {}  # To prevent race conditions when starting/stopping timers
logger.debug("Game timers dictionary initialized.")

WEBHOOK_ID = os.getenv('WEBHOOK_ID')
logger.debug(f"Webhook ID loaded: {WEBHOOK_ID}")


@bot.event
async def on_message(message):
    logger.info(f"Received message in channel '{message.channel}' from '{message.author}': {message.content}")

    # Check if the message is from a webhook
    if message.webhook_id:
        logger.info("Message is from a webhook.")
        # Check if the message starts with the command prefix
        if message.content.startswith(PREFIX):
            logger.info("Processing webhook message as a command.")
            # Create a context
            ctx = await bot.get_context(message)
            # Set the author to the bot's own member (the bot itself)
            ctx.author = message.guild.me
            # Process the command
            try:
                await bot.invoke(ctx)
                logger.info("Webhook command processed successfully.")
            except Exception as e:
                logger.error(f"Error processing webhook command: {e}", exc_info=True)
        return

    # Process regular user commands
    if message.content.startswith(PREFIX):
        try:
            await bot.process_commands(message)
            logger.info("User command processed successfully.")
        except Exception as e:
            logger.error(f"Error processing user command: {e}", exc_info=True)


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


@bot.event
async def on_guild_join(guild):
    """Initialize events for a guild only if they don't already exist."""
    logger.info(f"Bot joined new guild: {guild.name} (ID: {guild.id})")

    # Check if this guild already has events
    if not events_manager.guild_has_events(guild.id):
        events_manager.populate_events_for_guild(guild.id)
        logger.info(f"Populated events for new guild: {guild.name} (ID: {guild.id})")
    else:
        logger.info(f"Guild '{guild.name}' (ID: {guild.id}) already has events, skipping initialization.")

    # Send a welcome message to the system channel or the first text channel if available
    channel = guild.system_channel or next(
        (chan for chan in guild.text_channels if chan.permissions_for(guild.me).send_messages), None)
    if channel:
        await channel.send(f"Dota Timer Bot has been added to this server! Type `{PREFIX}bot-help` to get started.")
        logger.info(f"Sent welcome message to channel '{channel.name}' in guild '{guild.name}'.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing required arguments for this command.")
        logger.warning(f"Missing arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One or more arguments are invalid.")
        logger.warning(f"Bad arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Type `{PREFIX}bot-help` for a list of available commands.")
        logger.warning(f"Command not found. Context: {ctx.message.content}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")
        logger.warning(f"Permission denied for user '{ctx.author}'. Command: {ctx.command}")
    else:
        await ctx.send("An unexpected error occurred.")
        logger.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=True)


# Check: Admin permissions
def is_admin():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


# Load all cogs in the 'cogs' directory
async def load_cogs():
    logger.info("Loading cogs...")
    # Get only the relative path part for importing
    for filename in os.listdir(COGS_DIRECTORY):
        if filename.endswith('.py') and not filename.startswith('__'):
            # Build the import path using a relative path from `src.cogs`
            extension = f"src.cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                logger.info(f"Loaded cog: {extension}")
            except Exception as e:
                logger.error(f"Failed to load cog {extension}: {e}", exc_info=True)
    logger.info("All cogs loaded.")


# Reconnect Logic: Attempt to reconnect if disconnected from voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id:
        return

    guild = member.guild
    guild_id = guild.id

    # Check if the game is active for this guild
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        logger.info(f"Game is not active in guild '{guild.name}'. No reconnection attempt needed.")
        return

    # If the bot was disconnected and the game is active, attempt to reconnect
    if before.channel is not None and after.channel is None:
        logger.warning("Bot was disconnected from a voice channel. Attempting to reconnect...")
        dota_voice_channel = discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL_NAME)
        if dota_voice_channel:
            try:
                await dota_voice_channel.connect()
                logger.info(f"Reconnected to voice channel '{dota_voice_channel.name}' in guild '{guild.name}'.")
            except Exception as e:
                logger.error(
                    f"Failed to reconnect to voice channel '{dota_voice_channel.name}' in guild '{guild.name}': {e}",
                    exc_info=True
                )


# Command: Start game timer
@bot.command(name="start")
@commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
async def start_game(ctx, countdown: str, *args):
    logger.debug(f"Command '!start' invoked by '{ctx.author}' with countdown='{countdown}' and args={args}")
    guild_id = ctx.guild.id

    # Initialize a lock for this guild if not present
    if guild_id not in timer_locks:
        timer_locks[guild_id] = asyncio.Lock()

    async with timer_locks[guild_id]:
        try:
            # Validate that countdown is either MM:SS with optional leading '-' or a signed integer
            if not re.match(r"^-?\d+$", countdown) and not re.match(r"^-?\d{1,2}:\d{2}$", countdown):
                await ctx.send("Please enter a valid countdown format (MM:SS or signed integer in seconds).")
                logger.error(f"Invalid countdown format provided by '{ctx.author}'. Context: {ctx.message.content}")
                return
            logger.info(
                f"Inside start_game command: countdown='{countdown}', args={args}, guild_id={ctx.guild.id}, channel={ctx.channel.name}")

            # Determine mode based on args
            mode = 'regular'
            for arg in args:
                if arg.lower() in ['regular', 'turbo']:
                    mode = arg.lower()
                    logger.debug(f"Mode set to '{mode}' based on argument '{arg}'.")

            # Check if a timer is already running for this guild to ensure only one timer per guild
            if guild_id in game_timers and game_timers[guild_id].is_running():
                await ctx.send("A game timer is already running in this server.")
                logger.info(f"Game timer already running for guild ID {guild_id}. Start command ignored.")
                return

            # Find the voice channel
            dota_voice_channel = discord.utils.get(ctx.guild.voice_channels, name=VOICE_CHANNEL_NAME)
            if not dota_voice_channel:
                await ctx.send(f"'{VOICE_CHANNEL_NAME}' voice channel not found. Please create it and try again.")
                logger.warning(f"'{VOICE_CHANNEL_NAME}' voice channel not found in guild '{ctx.guild.name}'.")
                return
            else:
                logger.info(f"Found voice channel '{VOICE_CHANNEL_NAME}' in guild '{ctx.guild.name}'.")

            # Get the timer text channel
            timer_text_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
            if not timer_text_channel:
                await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
                logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
                return
            else:
                logger.info(f"Found text channel '{TIMER_CHANNEL_NAME}' in guild '{ctx.guild.name}'.")

            # Announce the start of the game timer
            await timer_text_channel.send(f"Starting {mode} game timer with countdown '{countdown}'.")
            logger.info(
                f"Starting game timer with mode='{mode}' and countdown='{countdown}' for guild ID {guild_id}.")

            # Initialize and start the GameTimer
            game_timer = GameTimer(guild_id, mode)
            game_timer.channel = timer_text_channel
            game_timers[guild_id] = game_timer
            logger.debug(f"GameTimer instance created and added to game_timers for guild ID {guild_id}.")

            # Connect to the voice channel
            voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice_client is None:
                voice_client = await dota_voice_channel.connect()
                logger.info(f"Connected to voice channel '{dota_voice_channel.name}' in guild '{ctx.guild.name}'.")
            elif voice_client.channel != dota_voice_channel:
                await voice_client.move_to(dota_voice_channel)
                logger.info(f"Moved voice client to '{dota_voice_channel.name}' in guild '{ctx.guild.name}'.")
            game_timer.voice_client = voice_client
            logger.debug(f"Voice client assigned to GameTimer for guild ID {guild_id}.")

            # Start the game timer with the countdown string directly
            await game_timer.start(timer_text_channel, countdown)
            logger.info(
                f"Game timer successfully started by '{ctx.author}' with countdown='{countdown}' and mode='{mode}' for guild ID {guild_id}.")

        except Exception as e:
            logger.error(f"Error in start_game command: {e}", exc_info=True)
            await ctx.send("An unexpected error occurred while starting the game timer.")


# Command: Stop game timer
@bot.command(name="stop")
async def stop_game(ctx):
    """Stop the game timer and all associated timers (Roshan, Glyph, Tormentor)."""
    logger.info(f"Command '!stop' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id

    # Initialize a lock for this guild if not present
    if guild_id not in timer_locks:
        timer_locks[guild_id] = asyncio.Lock()

    async with timer_locks[guild_id]:
        if guild_id in game_timers and game_timers[guild_id].is_running():
            timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
            if timer_channel:
                # Stop the game timer
                try:
                    await game_timers[guild_id].stop()
                    await timer_channel.send("Game timer stopped.")
                    logger.info(f"Game timer stopped by '{ctx.author}' for guild ID {guild_id}.")
                except Exception as e:
                    logger.error(f"Error stopping game timer for guild ID {guild_id}: {e}", exc_info=True)
                    await ctx.send("An error occurred while stopping the game timer.")

                # Remove the timer from the dictionary
                del game_timers[guild_id]
                logger.debug(f"GameTimer removed from game_timers for guild ID {guild_id}.")
            else:
                await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
                logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")
        else:
            await ctx.send("No active game timer found.")
            logger.warning(f"'{ctx.author}' attempted to stop the timer, but it was not running.")

        # Disconnect from the voice channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            try:
                await voice_client.disconnect()
                if guild_id in game_timers:
                    game_timers[guild_id].voice_client = None
                    logger.debug(f"Voice client disconnected for guild ID {guild_id}.")
                else:
                    logger.debug(f"Voice client disconnected for guild ID {guild_id}, but no GameTimer found.")
            except Exception as e:
                logger.error(f"Error disconnecting voice client for guild ID {guild_id}: {e}", exc_info=True)
        else:
            logger.warning("Voice client was not connected.")


# Command: Pause game timer
@bot.command(name="pause", aliases=['p'])
async def pause_game(ctx):
    """Pause the game timer and all events."""
    logger.info(f"Command '!pause' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id

    if guild_id in game_timers and game_timers[guild_id].is_running():
        if game_timers[guild_id].is_paused():
            await ctx.send("Game timer is already paused.")
            logger.warning(f"'{ctx.author}' attempted to pause the timer, but it was already paused.")
        else:
            try:
                await game_timers[guild_id].pause()
                await ctx.send("Game timer paused.")
                logger.info(f"Game timer and all child timers paused by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error pausing game timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while pausing the game timer.")
    else:
        await ctx.send("No active game timer found.")
        logger.warning(f"'{ctx.author}' attempted to pause the timer, but it was not running.")


# Command: Unpause game timer
@bot.command(name="unpause", aliases=['unp', 'up'])
async def unpause_game(ctx):
    """Resume the game timer and all events."""
    logger.info(f"Command '!unpause' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id

    if guild_id in game_timers and game_timers[guild_id].is_running():
        if not game_timers[guild_id].is_paused():
            await ctx.send("Game timer is not paused.")
            logger.warning(f"'{ctx.author}' attempted to unpause the timer, but it was not paused.")
        else:
            try:
                await game_timers[guild_id].unpause()
                await ctx.send("Game timer resumed.")
                logger.info(f"Game timer and all child timers resumed by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error unpausing game timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while resuming the game timer.")
    else:
        await ctx.send("No active game timer found.")
        logger.warning(f"'{ctx.author}' attempted to unpause the timer, but it was not running.")


# Command: Roshan timer
@bot.command(name="rosh", aliases=['rs', 'rsdead'])
async def rosh_timer_command(ctx):
    """Log Roshan's death and start the respawn timer."""
    logger.info(f"Command '!rosh' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.")
        logger.warning(f"Roshan timer attempted by '{ctx.author}' but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        roshan_timer = game_timers[guild_id].roshan_timer
        if not roshan_timer.is_running:
            try:
                await roshan_timer.start(timer_channel)
                await timer_channel.send("Roshan timer started.")
                logger.info(f"Roshan timer started by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error starting Roshan timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while starting the Roshan timer.")
        else:
            await ctx.send("Roshan timer is already running.")
            logger.warning(f"'{ctx.author}' attempted to start Roshan timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")


# Command: Cancel Roshan timer
@bot.command(name='cancel-rosh', aliases=['rsalive', 'rsback', 'rsb'])
async def cancel_rosh_command(ctx):
    """Cancel the Roshan respawn timer."""
    logger.info(f"Command '!cancel-rosh' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        roshan_timer = game_timers[guild_id].roshan_timer
        if roshan_timer.is_running:
            try:
                await roshan_timer.stop()
                await timer_channel.send("Roshan timer has been cancelled.")
                logger.info(f"Roshan timer cancelled by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error cancelling Roshan timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while cancelling the Roshan timer.")
        else:
            await ctx.send("No active Roshan timer to cancel.")
            logger.warning(f"No active Roshan timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.")
        logger.warning(f"'{ctx.author}' attempted to cancel Roshan timer, but game timer is not active.")


# Command: Glyph cooldown timer
@bot.command(name="glyph", aliases=['g'])
async def glyph_timer_command(ctx):
    """Start the Glyph cooldown timer."""
    logger.info(f"Command '!glyph' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.")
        logger.warning(f"Glyph timer attempted by '{ctx.author}' but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        glyph_timer = game_timers[guild_id].glyph_timer
        if not glyph_timer.is_running:
            try:
                await glyph_timer.start(timer_channel)
                await timer_channel.send("Glyph timer started.")
                logger.info(f"Glyph timer started by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error starting Glyph timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while starting the Glyph timer.")
        else:
            await ctx.send("Glyph timer is already running.")
            logger.warning(f"'{ctx.author}' attempted to start Glyph timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logger.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")


# Command: Cancel Glyph timer
@bot.command(name="cancel-glyph", aliases=['cg'])
async def cancel_glyph_command(ctx):
    """Cancel the Glyph cooldown timer."""
    logger.info(f"Command '!cancel-glyph' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        glyph_timer = game_timers[guild_id].glyph_timer
        if glyph_timer.is_running:
            try:
                await glyph_timer.stop()
                await timer_channel.send("Glyph timer has been cancelled.")
                logger.info(f"Glyph timer cancelled by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error cancelling Glyph timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while cancelling the Glyph timer.")
        else:
            await ctx.send("No active Glyph timer to cancel.")
            logger.warning(f"No active Glyph timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.")
        logger.warning(f"'{ctx.author}' attempted to cancel Glyph timer, but game timer is not active.")


# Command: Tormentor timer
@bot.command(name="tormentor", aliases=['tm', 'torm', 't'])
async def tormentor_timer_command(ctx):
    """Log Tormentor's death and start the respawn timer."""
    logger.info(f"Command '!tormentor' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    if guild_id not in game_timers or not game_timers[guild_id].is_running():
        await ctx.send("Game is not active.")
        logger.warning(f"Tormentor timer attempted by '{ctx.author}' but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        tormentor_timer = game_timers[guild_id].tormentor_timer
        if not tormentor_timer.is_running:
            try:
                await tormentor_timer.start(timer_channel)
                await timer_channel.send("Tormentor timer started.")
                logger.info(f"Tormentor timer started by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error starting Tormentor timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while starting the Tormentor timer.")
        else:
            await ctx.send("Tormentor timer is already running.")
            logger.warning(f"'{ctx.author}' attempted to start Tormentor timer, but it was already running.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create one and try again.")
        logger.warning(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")


# Command: Cancel Tormentor timer
@bot.command(name="cancel-torm", aliases=['ct', 'tormentorcancel'])
async def cancel_tormentor_command(ctx):
    """Cancel the Tormentor respawn timer."""
    logger.info(f"Command '!cancel-torm' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if guild_id in game_timers:
        tormentor_timer = game_timers[guild_id].tormentor_timer
        if tormentor_timer.is_running:
            try:
                await tormentor_timer.stop()
                await timer_channel.send("Tormentor timer has been cancelled.")
                logger.info(f"Tormentor timer cancelled by '{ctx.author}' for guild ID {guild_id}.")
            except Exception as e:
                logger.error(f"Error cancelling Tormentor timer for guild ID {guild_id}: {e}", exc_info=True)
                await ctx.send("An error occurred while cancelling the Tormentor timer.")
        else:
            await ctx.send("No active Tormentor timer to cancel.")
            logger.warning(f"No active Tormentor timer found to cancel for guild ID {guild_id}.")
    else:
        await ctx.send("Game timer is not active.")
        logger.warning(f"'{ctx.author}' attempted to cancel Tormentor timer, but game timer is not active.")


# Command: Add custom event
@bot.command(name="add-event")
async def add_event_command(ctx, event_type: str, *args):
    """
    Add a custom event.
    Usage:
    - For static events: !add-event static <MM:SS> <message>
    - For periodic events: !add-event periodic <MM:SS> <MM:SS> <MM:SS> <message>
    """
    logger.info(f"Command '!add-event' invoked by '{ctx.author}' with event_type='{event_type}' and args={args}")
    guild_id = ctx.guild.id
    try:
        if event_type.lower() == 'static':
            if len(args) < 2:
                await ctx.send(
                    "Insufficient arguments for static event. Usage: `!add-event static <MM:SS> <message>`")
                logger.warning(f"Insufficient arguments for static event by '{ctx.author}'.")
                return
            time_str = args[0]
            message = ' '.join(args[1:])
            time_seconds = min_to_sec(time_str)
            event_id = events_manager.add_static_event(guild_id, time_seconds, message)
            await ctx.send(f"Static event added with ID {event_id}.")
            logger.info(f"Static event added with ID {event_id} by '{ctx.author}' for guild ID {guild_id}.")

        elif event_type.lower() == 'periodic':
            if len(args) < 4:
                await ctx.send(
                    "Insufficient arguments for periodic event. Usage: `!add-event periodic <MM:SS> <MM:SS> <MM:SS> <message>`")
                logger.warning(f"Insufficient arguments for periodic event by '{ctx.author}'.")
                return
            start_time_str = args[0]
            interval_str = args[1]
            end_time_str = args[2]
            message = ' '.join(args[3:])
            start_time = min_to_sec(start_time_str)
            interval = min_to_sec(interval_str)
            end_time = min_to_sec(end_time_str)
            event_id = events_manager.add_periodic_event(guild_id, start_time, interval, end_time, message)
            await ctx.send(f"Periodic event added with ID {event_id}.")
            logger.info(f"Periodic event added with ID {event_id} by '{ctx.author}' for guild ID {guild_id}.")

        else:
            await ctx.send("Invalid event type. Use 'static' or 'periodic'.")
            logger.warning(f"Invalid event type '{event_type}' used by '{ctx.author}'.")
    except ValueError:
        await ctx.send("Invalid time format. Please use MM:SS format.")
        logger.error(f"Invalid time format used by '{ctx.author}' with args={args}.")
    except Exception as e:
        await ctx.send(f"Error adding event: {e}")
        logger.error(f"Error adding event by '{ctx.author}': {e}", exc_info=True)


# Command: Remove custom event
@bot.command(name="remove-event")
@is_admin()
async def remove_event_command(ctx, event_id: int):
    """Remove a custom event by its ID."""
    logger.info(f"Command '!remove-event' invoked by '{ctx.author}' with event_id={event_id}")
    guild_id = ctx.guild.id
    try:
        success = events_manager.remove_event(guild_id, event_id)
        if success:
            await ctx.send(f"Event ID {event_id} removed.")
            logger.info(f"Event ID {event_id} removed by '{ctx.author}' for guild ID {guild_id}.")
        else:
            await ctx.send(f"No event found with ID {event_id}.")
            logger.warning(f"Event ID {event_id} not found for removal by '{ctx.author}' in guild ID {guild_id}.")
    except Exception as e:
        await ctx.send(f"Error removing event: {e}")
        logger.error(f"Error removing event ID {event_id} by '{ctx.author}' for guild ID {guild_id}: {e}",
                     exc_info=True)


# Command: List custom events
@bot.command(name="list-events", aliases=['ls', 'events'])
async def list_events_command(ctx):
    """List all custom events for the current guild."""
    logger.info(f"Command '!list-events' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id

    # Retrieve events specific to this guild
    static_events = events_manager.get_static_events(guild_id)
    periodic_events = events_manager.get_periodic_events(guild_id)

    # Check if any events exist
    if not static_events and not periodic_events:
        await ctx.send("No custom events found for this guild.")
        logger.info(f"No custom events found for guild ID {guild_id}.")
        return

    # Create an embed message for better readability
    embed = discord.Embed(title=f"Events for Guild: {ctx.guild.name}", color=0x00ff00)
    logger.debug(f"Creating embed for events in guild ID {guild_id}.")

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
            logger.debug(f"Added static event ID {event_id} to embed.")

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
            logger.debug(f"Added periodic event ID {event_id} to embed.")

    # Send the embed message with the events list
    await ctx.send(embed=embed)
    logger.info(f"Events listed for guild '{ctx.guild.name}' (ID: {guild_id}).")


# Command: Reset events
@bot.command(name="reset-events")
async def reset_events_command(ctx):
    """Reset all events for the guild to default settings."""
    logger.info(f"Command '!reset-events' invoked by '{ctx.author}'")
    guild_id = ctx.guild.id
    try:
        # Delete all events associated with this guild
        events_manager.delete_events_for_guild(guild_id)
        logger.info(f"All events deleted for guild ID {guild_id} by '{ctx.author}'.")

        # Repopulate with default events
        events_manager.populate_events_for_guild(guild_id)
        logger.info(f"Default events populated for guild ID {guild_id} by '{ctx.author}'.")

        await ctx.send("All events have been reset to default settings for this guild.")
    except Exception as e:
        await ctx.send("An error occurred while resetting events.")
        logger.error(f"Error resetting events for guild ID {guild_id} by '{ctx.author}': {e}", exc_info=True)


# Command: Enable mindful messages
@bot.command(name="enable-mindful", aliases=['enable-pma', 'pma'])
async def enable_mindful_messages(ctx):
    guild_id = ctx.guild.id
    try:
        events_manager.set_mindful_messages(guild_id, enabled=True)
        await ctx.send("Mindful messages have been enabled.")
        logger.info(f"Mindful messages enabled by '{ctx.author}' in guild ID {guild_id}.")
    except Exception as e:
        await ctx.send("An error occurred while enabling mindful messages.")
        logger.error(f"Error enabling mindful messages for guild ID {guild_id} by '{ctx.author}': {e}", exc_info=True)


# Command: Disable mindful messages
@bot.command(name="disable-mindful", aliases=['disable-pma', 'no-pma'])
async def disable_mindful_messages(ctx):
    guild_id = ctx.guild.id
    try:
        events_manager.set_mindful_messages(guild_id, enabled=False)
        await ctx.send("Mindful messages have been disabled.")
        logger.info(f"Mindful messages disabled by '{ctx.author}' in guild ID {guild_id}.")
    except Exception as e:
        await ctx.send("An error occurred while disabling mindful messages.")
        logger.error(f"Error disabling mindful messages for guild ID {guild_id} by '{ctx.author}': {e}", exc_info=True)


# Command: Kill all game timers across all guilds
@bot.command(name="killall")
@is_admin()
async def kill_all_game_timers(ctx):
    """Stop all game timers across all guilds."""
    logger.info(f"Command '!killall' invoked by '{ctx.author}'")
    guild_ids = list(game_timers.keys())
    if not guild_ids:
        await ctx.send("There are no active game timers to kill.")
        logger.info("No active game timers found to kill.")
        return

    for guild_id in guild_ids:
        timer_lock = timer_locks.get(guild_id)
        if timer_lock:
            async with timer_lock:
                timer = game_timers.get(guild_id)
                if timer and timer.is_running():
                    try:
                        await timer.stop()
                        # Send a message to the guild's timer channel
                        guild = bot.get_guild(guild_id)
                        if guild:
                            timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
                            if timer_channel:
                                await timer_channel.send("Game timer has been forcefully stopped by an admin.")
                                logger.info(f"Game timer forcefully stopped in guild '{guild.name}' by '!killall'.")
                        # Disconnect from voice channel
                        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
                        if voice_client:
                            await voice_client.disconnect()
                            logger.info(f"Disconnected from voice channel in guild '{guild.name}'.")
                        # Remove from game_timers
                        del game_timers[guild_id]
                    except Exception as e:
                        logger.error(f"Error killing game timer for guild ID {guild_id}: {e}", exc_info=True)
    await ctx.send("All game timers have been stopped.")
    logger.info("All game timers have been killed by '!killall'.")


# Graceful shutdown handling
async def shutdown():
    logger.info("Initiating bot shutdown...")

    # Stop all game timers quickly
    logger.info("Stopping all game timers.")
    for guild_id, timer in list(game_timers.items()):
        try:
            await asyncio.wait_for(timer.stop(), timeout=2)  # Set a shorter timeout for each stop call
            logger.info(f"Stopped GameTimer for guild ID {guild_id}.")
        except asyncio.TimeoutError:
            logger.warning(f"Timer for guild ID {guild_id} took too long to stop; forced stop.")
        except Exception as e:
            logger.error(f"Error stopping GameTimer for guild ID {guild_id}: {e}", exc_info=True)

    # Disconnect all voice clients with a timeout
    logger.info("Disconnecting all voice clients.")
    disconnect_tasks = [vc.disconnect() for vc in bot.voice_clients]
    try:
        await asyncio.wait_for(asyncio.gather(*disconnect_tasks), timeout=5)  # Disconnect all within 5 seconds
        logger.info("All voice clients disconnected.")
    except asyncio.TimeoutError:
        logger.warning("Some voice clients did not disconnect within the timeout.")
    except Exception as e:
        logger.error(f"Error disconnecting voice clients: {e}", exc_info=True)

    # Close the EventsManager session quickly
    events_manager.close()
    logger.debug("EventsManager session closed.")

    await bot.close()  # Properly close the bot
    logger.info("Bot has been shut down.")


# Handle termination signals for graceful shutdown
def handle_signal(sig):
    logger.info(f"Received exit signal {sig.name}...")
    asyncio.create_task(shutdown())


# Register signal handlers
signal.signal(signal.SIGINT, lambda s, f: handle_signal(signal.Signals.SIGINT))
signal.signal(signal.SIGTERM, lambda s, f: handle_signal(signal.Signals.SIGTERM))
logger.debug("Signal handlers registered.")


# Main entry point
async def main():
    async with bot:
        await load_cogs()
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            logger.error("Bot token not found. Please set the 'DISCORD_BOT_TOKEN' environment variable.")
            return
        logger.info("Starting bot...")
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
