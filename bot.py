import discord
from discord.ext import commands
from timer import GameTimer
import os

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content if your bot reads message content

# Initialize the bot with intents
bot = commands.Bot(command_prefix='!', intents=intents)
game_timer = GameTimer()

# Channel name for all timer messages
TIMER_CHANNEL_NAME = "timer-bot"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    # Find the "timer-bot" channel
    for guild in bot.guilds:
        timer_channel = discord.utils.get(guild.text_channels, name=TIMER_CHANNEL_NAME)
        if timer_channel:
            print(f"Timer bot channel found: {timer_channel.name}")
        else:
            print(f"No channel named '{TIMER_CHANNEL_NAME}' found in {guild.name}. Please create one.")
            return

@bot.command()
async def startgame(ctx, countdown: int, *usernames):
    if len(usernames) != 5:
        await ctx.send("Please provide exactly 5 usernames.")
        return

    # Use the timer channel for messages
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await timer_channel.send(f"Starting game timer with players: {', '.join(usernames)}")
        await game_timer.start(timer_channel, countdown, usernames)
    else:
        await ctx.send(f"No channel named '{TIMER_CHANNEL_NAME}' found. Please create it and try again.")

@bot.command()
async def stopgame(ctx):
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        await game_timer.stop()
        await timer_channel.send("Game timer stopped.")
    else:
        await ctx.send(f"No channel named '{TIMER_CHANNEL_NAME}' found. Please create it and try again.")

@bot.command()
async def add_event(ctx, time: str, interval: str, end_time: str, message: str, *target_groups):
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.add_periodic_event(time, interval, end_time, message, target_groups)
        await timer_channel.send(
            f"Added periodic event '{message}' every {interval} starting at {time} ending at {end_time} for {', '.join(target_groups)}"
        )
    else:
        await ctx.send(f"No channel named '{TIMER_CHANNEL_NAME}' found. Please create it and try again.")

@bot.command()
async def remove_event(ctx, message: str):
    timer_channel = discord.utils.get(ctx.guild.text_channels, name=TIMER_CHANNEL_NAME)
    if timer_channel:
        game_timer.remove_event(message)
        await timer_channel.send(f"Removed event '{message}'")
    else:
        await ctx.send(f"No channel named '{TIMER_CHANNEL_NAME}' found. Please create it and try again.")

# Run the bot using the token stored in the environment variable
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
