import discord
from discord import app_commands
from discord.ext import commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from timer import GameTimer
from roshan import RoshanTimer
from events import EVENTS, PERIODIC_EVENTS

# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Instantiate timers
game_timer = GameTimer()
roshan_timer = RoshanTimer()

# Constants
TIMER_CHANNEL_NAME = "timer-bot"
TESTING_GUILD_ID = YOUR_GUILD_ID  # Replace with your guild's ID
testing_guild = discord.Object(id=TESTING_GUILD_ID)

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
    try:
        await bot.tree.sync(guild=testing_guild)
        print(f"Commands synced to guild {TESTING_GUILD_ID}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Slash Commands
@bot.tree.command(name="startgame", description="Start the game timer with a countdown and player usernames.", guild=testing_guild)
async def startgame(interaction: discord.Interaction, countdown: int, username1: str, username2: str, username3: str, username4: str, username5: str):
    """Start the game timer with a countdown and 5 player usernames."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    usernames = [username1, username2, username3, username4, username5]

    if timer_channel:
        await timer_channel.send(f"Starting game timer with players: {', '.join(usernames)}")
        await game_timer.start(timer_channel, countdown, usernames)
        await interaction.response.send_message("Game timer started.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.tree.command(name="stopgame", description="Stop the game timer.")
async def stopgame(interaction: discord.Interaction):
    """Stop the game timer."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await game_timer.stop()
        await timer_channel.send("Game timer stopped.")
        await interaction.response.send_message("Game timer stopped.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.tree.command(name="rosh", description="Log Roshan's death and start the respawn timer.")
async def rosh(interaction: discord.Interaction):
    """Log Roshan's death and start the respawn timer."""
    if not game_timer.is_running():
        await interaction.response.send_message("Game is not active.", ephemeral=True)
        return

    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    await roshan_timer.start(timer_channel)
    await interaction.response.send_message("Roshan timer started.", ephemeral=True)

@bot.tree.command(name="add_static_event", description="Add a static event.")
async def add_static_event(interaction: discord.Interaction, time: str, message: str, target_group: str):
    """Add a static event with a specified time and message."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.add_event(time, message, target_group)
        await timer_channel.send(f"Added static event '{message}' at {time} for {target_group}.")
        await interaction.response.send_message(f"Added static event '{message}' at {time}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.tree.command(name="add_periodic_event", description="Add a periodic event.")
async def add_periodic_event(interaction: discord.Interaction, start_time: str, interval: str, end_time: str, message: str, target_group: str):
    """Add a periodic event with start time, interval, end time, and message."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.add_custom_event(start_time, interval, end_time, message, [target_group])
        await timer_channel.send(f"Added periodic event '{message}' every {interval} starting at {start_time} until {end_time} for {target_group}.")
        await interaction.response.send_message(f"Added periodic event '{message}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.tree.command(name="remove_event", description="Remove an event by message.")
async def remove_event(interaction: discord.Interaction, message: str):
    """Remove an event by its message."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.remove_custom_event(message)
        await timer_channel.send(f"Removed event '{message}'.")
        await interaction.response.send_message(f"Removed event '{message}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.tree.command(name="list_events", description="List all currently set events.")
async def list_events(interaction: discord.Interaction):
    """List all events currently set in the game."""
    timer_channel = discord.utils.get(interaction.guild.text_channels, name=TIMER_CHANNEL_NAME)
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
            await interaction.response.send_message("Listed all events.", ephemeral=True)
        else:
            await timer_channel.send("No events set.")
            await interaction.response.send_message("No events set.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Channel '{TIMER_CHANNEL_NAME}' not found. Please create it and try again.", ephemeral=True)

@bot.command(name="bot-help")
async def bot_help(ctx):
    """Show available commands with examples."""
    commands_info = (
        "`!startgame <countdown> <username1> <username2> <username3> <username4> <username5>` - Start game timer with 5 players.\n"
        "`!stopgame` - Stop the game timer.\n"
        "`!rosh` - Log Roshan's death and start an 8-minute timer.\n"
        "`!add_static_event <time:00:00> <message> <target_group>` - Add a static event.\n"
        "`!add_periodic_event <start_time:00:00> <interval:00:00> <end_time:00:00> <message> <target_group>` - Add a periodic event.\n"
        "`!remove_event <message>` - Remove an event by message.\n"
        "`!list_events` - List all currently set events.\n"
        "`!bot-help` - Show this help message."
    )
    await ctx.send(commands_info)

# Start the HTTP server in a separate thread
threading.Thread(target=run_server, daemon=True).start()

# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))