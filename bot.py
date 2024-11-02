import discord
from discord.ext import commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from timer import GameTimer
from roshan import RoshanTimer
from events import EVENTS, PERIODIC_EVENTS

# Initialize intents and bot, disabling the default help command
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

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
    httpd.serve_forever()

# Event handlers
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for guild in bot.guilds:
        timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
        if not timer_channel:
            print(f"Channel '{TIMER_CHANNEL_NAME}' not found in {guild.name}. Please create it.")

# Commands
@bot.command()
async def startgame(ctx, countdown: int, *usernames):
    """Start the game timer with a countdown and player usernames."""
    if len(usernames) != 5:
        await ctx.send("Please provide exactly 5 usernames.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send(f"Starting game timer with players: {', '.join(usernames)}")
        await game_timer.start(timer_channel, countdown, usernames)
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")

@bot.command()
async def stopgame(ctx):
    """Stop the game timer."""
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await game_timer.stop()
        await timer_channel.send("Game timer stopped.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")

@bot.command()
async def rosh(ctx):
    """Log Roshan's death and start the respawn timer."""
    if not game_timer.is_running():
        await ctx.send("Game is not active.")
        return

    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    await roshan_timer.start(timer_channel)

@bot.command()
async def add_event(ctx, start_time: str, interval: str, end_time: str, message: str, *target_groups):
    """Add a custom periodic event."""
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.add_custom_event(start_time, interval, end_time, message, target_groups)
        await timer_channel.send(
            f"Added event '{message}' every {interval}, from {start_time} to {end_time}, for {', '.join(target_groups)}."
        )
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")

@bot.command()
async def remove_event(ctx, *, message: str):
    """Remove a custom event by message."""
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.remove_custom_event(message)
        await timer_channel.send(f"Removed event '{message}'.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")

@bot.command()
async def list_events(ctx):
    """List all currently set events."""
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        messages = []

        # List static events
        for time, (msg, _) in EVENTS.items():
            messages.append(f"Static Event - {time}: {msg}")

        # List periodic events
        for start, interval, end, (msg, _) in PERIODIC_EVENTS:
            messages.append(f"Periodic Event - {start} every {interval} until {end}: {msg}")

        # List custom events
        custom_events = game_timer.get_custom_events()
        for event in custom_events:
            messages.append(
                f"Custom Event - starts at {event['start_time']} every {event['interval']} until {event['end_time']}: {event['message']}"
            )

        if messages:
            await timer_channel.send("\n".join(messages))
        else:
            await timer_channel.send("No events set.")
    else:
        await ctx.send(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.")

@bot.command(name="help")
async def custom_help(ctx):
    """Show available commands."""
    commands_info = (
        "`!startgame <countdown> <username1> <username2> ...` - Start game timer with 5 players.\n"
        "`!stopgame` - Stop the game timer.\n"
        "`!rosh` - Log Roshan's death and start an 8-minute timer.\n"
        "`!add_event <start_time> <interval> <end_time> <message> <target_groups>` - Add a custom event.\n"
        "`!remove_event <message>` - Remove a custom event by message.\n"
        "`!list_events` - List all currently set events.\n"
        "`!help` - Show this help message."
    )
    await ctx.send(commands_info)

# Start the HTTP server in a separate thread
threading.Thread(target=run_server, daemon=True).start()

# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
