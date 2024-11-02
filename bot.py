import discord
from discord.ext import commands
from timer import GameTimer
import os

# Initialize the bot
bot = commands.Bot(command_prefix='!')
game_timer = GameTimer()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def startgame(ctx, countdown: int, *usernames):
    if len(usernames) != 5:
        await ctx.send("Please provide exactly 5 usernames.")
        return

    await ctx.send(f"Starting game timer with players: {', '.join(usernames)}")
    await game_timer.start(ctx, countdown, usernames)


@bot.command()
async def stopgame(ctx):
    await game_timer.stop()
    await ctx.send("Game timer stopped.")


@bot.command()
async def add_event(ctx, time: str, interval: str, end_time: str, message: str, *target_groups):
    game_timer.add_periodic_event(time, interval, end_time, message, target_groups)
    await ctx.send(
        f"Added periodic event '{message}' every {interval} starting at {time} ending at {end_time} for {', '.join(target_groups)}")


@bot.command()
async def remove_event(ctx, message: str):
    game_timer.remove_event(message)
    await ctx.send(f"Removed event '{message}'")


bot.run(os.getenv('DISCORD_BOT_TOKEN'))
