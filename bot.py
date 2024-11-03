# bot.py

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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Instantiate timers
game_timer = GameTimer()
roshan_timer = RoshanTimer()

# Constants
TIMER_CHANNEL_NAME = "timer-bot"

# HTTP server to keep bot alive
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

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
        await ctx.send("❌ You are missing required arguments for this command.")
        logging.warning(f"Missing arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ One or more arguments are invalid.")
        logging.warning(f"Bad arguments in command '{ctx.command}'. Context: {ctx.message.content}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Type `!bot-help` for a list of available commands.")
        logging.warning(f"Command not found. Context: {ctx.message.content}")
    else:
        await ctx.send("❌ An error occurred while processing the command.")
        logging.error(f"Unhandled error in command '{ctx.command}': {error}")

# Commands
@bot.command(name="startgame")
async def startgame(ctx, countdown: int, *usernames):
    """Start the game timer with a countdown and player usernames."""
    logging.info(f"Command '!startgame' invoked by {ctx.author} with countdown={countdown} and usernames={usernames}")
    if len(usernames) != 5:
        await ctx.send("❌ Please provide exactly 5 usernames.")
        logging.warning(f"Incorrect number of usernames provided by {ctx.author}. Provided: {len(usernames)}")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send(f"🕒 Starting game timer with players: {', '.join(usernames)}")
        await game_timer.start(timer_channel, countdown, usernames)
        logging.info(f"Game timer started by {ctx.author} with countdown={countdown} and usernames={usernames}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="stopgame")
async def stopgame(ctx):
    """Stop the game timer."""
    logging.info(f"Command '!stopgame' invoked by {ctx.author}")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await game_timer.stop()
        await timer_channel.send("🛑 Game timer stopped.")
        logging.info(f"Game timer stopped by {ctx.author}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="rosh")
async def rosh(ctx):
    """Log Roshan's death and start the respawn timer."""
    logging.info(f"Command '!rosh' invoked by {ctx.author}")
    if not game_timer.is_running():
        await ctx.send("❌ Game is not active.")
        logging.warning(f"Roshan timer attempted by {ctx.author} but game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await roshan_timer.start(timer_channel)
        logging.info(f"Roshan timer started by {ctx.author}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="glyph")
async def glyph(ctx):
    """Start a 5-minute timer for the enemy's glyph cooldown."""
    logging.info(f"Command '!glyph' invoked by {ctx.author}")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send("🛡️ **Enemy glyph used!** Starting 5-minute cooldown timer.")
        await game_timer.start_glyph_timer(timer_channel)
        logging.info(f"Glyph timer started by {ctx.author}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="add-static-event")
async def add_static_event(ctx, time: str, message: str, target_group: str):
    """Add a static event."""
    logging.info(f"Command '!add-static-event' invoked by {ctx.author} with time={time}, message='{message}', target_group='{target_group}'")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        try:
            event_id = game_timer.add_event(time, message, target_group)
            await timer_channel.send(f"✅ Added static event '{message}' with ID `{event_id}` at {time} for `{target_group}`.")
            logging.info(f"Static event added by {ctx.author}: ID={event_id}, time={time}, message='{message}', target_group='{target_group}'")
        except ValueError as ve:
            await ctx.send(f"❌ {ve}")
            logging.error(f"Error adding static event: {ve}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="add-periodic-event")
async def add_periodic_event(ctx, start_time: str, interval: str, end_time: str, message: str, target_group: str):
    """Add a periodic event."""
    logging.info(f"Command '!add-periodic-event' invoked by {ctx.author} with start_time={start_time}, interval={interval}, end_time={end_time}, message='{message}', target_group='{target_group}'")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        try:
            event_id = game_timer.add_custom_event(start_time, interval, end_time, message, [target_group])
            await timer_channel.send(
                f"✅ Added periodic event '{message}' with ID `{event_id}` every `{interval}`, from `{start_time}` to `{end_time}`, for `{target_group}`."
            )
            logging.info(f"Periodic event added by {ctx.author}: ID={event_id}, start_time={start_time}, interval={interval}, end_time={end_time}, message='{message}', target_group='{target_group}'")
        except ValueError as ve:
            await ctx.send(f"❌ {ve}")
            logging.error(f"Error adding periodic event: {ve}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="remove-event")
async def remove_event(ctx, event_id: int):
    """Remove an event by its unique ID."""
    logging.info(f"Command '!remove-event' invoked by {ctx.author} with event_id={event_id}")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        # First, attempt to remove from static EVENTS
        if event_id in STATIC_EVENTS:
            del STATIC_EVENTS[event_id]
            await timer_channel.send(f"✅ Removed static event ID `{event_id}`.")
            logging.info(f"Static event ID {event_id} removed by {ctx.author}")
            return

        # Next, attempt to remove from custom_events
        removed = game_timer.remove_custom_event(event_id)
        if removed:
            await timer_channel.send(f"✅ Removed custom event ID `{event_id}`.")
            logging.info(f"Custom event ID {event_id} removed by {ctx.author}")
        else:
            await ctx.send(f"❌ Event with ID `{event_id}` not found.")
            logging.warning(f"Attempted to remove non-existent event ID {event_id} by {ctx.author}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="list-events")
async def list_events(ctx):
    """List all currently set events."""
    logging.info(f"Command '!list-events' invoked by {ctx.author}")
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        messages = []

        # List static events
        for event_id, event in STATIC_EVENTS.items():
            messages.append(f"🟢 **Static Event** | ID: `{event_id}` | Time: `{event['time']}` | Message: {event['message']} | Targets: `{', '.join(event['target_groups'])}`")

        # List predefined periodic events
        for event_id, event in PERIODIC_EVENTS.items():
            messages.append(f"🔄 **Predefined Periodic Event** | ID: `{event_id}` | Start: `{event['start_time']}` | Interval: `{event['interval']}` | End: `{event['end_time']}` | Message: {event['message']} | Targets: `{', '.join(event['target_groups'])}`")

        # List custom events
        custom_events = game_timer.get_custom_events()
        for event_id, event in custom_events.items():
            start_time_formatted = f"{event['start_time'] // 60:02}:{event['start_time'] % 60:02}"
            end_time_formatted = f"{event['end_time'] // 60:02}:{event['end_time'] % 60:02}"
            interval_formatted = f"{event['interval'] // 60:02}:{event['interval'] % 60:02}"
            messages.append(f"🔁 **Custom Periodic Event** | ID: `{event_id}` | Start: `{start_time_formatted}` | Interval: `{interval_formatted}` | End: `{end_time_formatted}` | Message: {event['message']} | Targets: `{', '.join(event['target_groups'])}`")

        if messages:
            embed = discord.Embed(
                title="📜 Current Events",
                description="\n".join(messages),
                color=0x00ff00
            )
            await timer_channel.send(embed=embed)
            logging.info(f"Listed events for {ctx.author}")
        else:
            await timer_channel.send("ℹ️ No events set.")
            logging.info(f"No events to list for {ctx.author}")
    else:
        await ctx.send(f"❌ Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")
        logging.error(f"Channel '{TIMER_CHANNEL_NAME}' not found in guild '{ctx.guild.name}'.")

@bot.command(name="bot-help")
async def bot_help(ctx):
    """Show available commands with examples."""
    logging.info(f"Command '!bot-help' invoked by {ctx.author}")
    embed = discord.Embed(
        title="📜 Dota Timer Bot - Help",
        description="Here are the available commands with examples:",
        color=0x00ff00
    )
    embed.add_field(
        name="!startgame",
        value="`!startgame <countdown> <username1> <username2> <username3> <username4> <username5>`\nStarts the game timer with a countdown and 5 players.\n**Example:** `!startgame 3 @martinlol @alice @bob @jane @john`",
        inline=False
    )
    embed.add_field(
        name="!stopgame",
        value="`!stopgame`\nStops the current game timer.\n**Example:** `!stopgame`",
        inline=False
    )
    embed.add_field(
        name="!rosh",
        value="`!rosh`\nLogs Roshan's death and starts an 8-minute respawn timer.\n**Example:** `!rosh`",
        inline=False
    )
    embed.add_field(
        name="!add-static-event",
        value="`!add-static-event <time:MM:SS> <message> <target_group>`\nAdds a static event.\n**Example:** `!add-static-event 10:00 \"Power Rune spawned!\" mid`",
        inline=False
    )
    embed.add_field(
        name="!add-periodic-event",
        value="`!add-periodic-event <start_time:MM:SS> <interval:MM:SS> <end_time:MM:SS> <message> <target_group>`\nAdds a periodic event.\n**Example:** `!add-periodic-event 06:40 02:00 40:00 \"XP runes spawning soon\" all`",
        inline=False
    )
    embed.add_field(
        name="!remove-event",
        value="`!remove-event <event_id>`\nRemoves an event by its unique ID.\n**Example:** `!remove-event 5`",
        inline=False
    )
    embed.add_field(
        name="!list-events",
        value="`!list-events`\nLists all currently set events.\n**Example:** `!list-events`",
        inline=False
    )
    embed.add_field(
        name="!bot-help",
        value="`!bot-help`\nShows this help message.\n**Example:** `!bot-help`",
        inline=False
    )
    await ctx.send(embed=embed)
    logging.info(f"Help message sent to {ctx.author}")

# Start the HTTP server in a separate thread
threading.Thread(target=run_server, daemon=True).start()
logging.info("HTTP server thread started.")

# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
