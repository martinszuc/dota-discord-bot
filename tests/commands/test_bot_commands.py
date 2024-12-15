# tests/commands/test_bot_commands.py
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from discord.ext import commands


@pytest.fixture
def test_bot():
    """Create a bot instance for testing."""
    intents = discord.Intents.default()
    intents.message_content = True  # Enable required intents
    bot = commands.Bot(command_prefix='!', intents=intents)

    # Import the command function and add it to the bot
    from src.bot import start_game
    bot.add_command(start_game)

    return bot

@pytest.fixture
def ctx():
    """Create a mock context."""
    mock_ctx = Mock()
    mock_ctx.send = AsyncMock()
    mock_ctx.guild = Mock()
    mock_ctx.guild.id = 123456789
    mock_ctx.guild.name = "TestGuild"
    mock_ctx.author = Mock()
    mock_ctx.author.guild_permissions = Mock(administrator=True)
    mock_ctx.author.name = "TestUser"
    mock_ctx.channel = AsyncMock()  # Mock the channel
    return mock_ctx

@pytest.mark.asyncio
async def test_start_command_success(test_bot, ctx):
    """Test the !start command with valid inputs."""
    with patch('src.bot.GameTimer') as MockGameTimer, \
         patch('discord.utils.get') as mock_get, \
         patch('discord.ext.commands.Bot.load_extension', new=AsyncMock()):

        # Mock the Timer and Channels
        mock_timer = AsyncMock()  # Use AsyncMock for async methods
        mock_timer.is_running.return_value = False
        MockGameTimer.return_value = mock_timer

        mock_voice_channel = AsyncMock()
        mock_text_channel = AsyncMock()

        # Now provide three return values:
        # 1) voice channel by name
        # 2) text channel by name
        # 3) voice client lookup returns None
        mock_get.side_effect = [mock_voice_channel, mock_text_channel, None]

        command = test_bot.get_command('start')
        assert command is not None, "The 'start' command was not registered."

        await command(ctx, "10:00", "regular")

        # Check calls
        mock_get.assert_any_call(ctx.guild.voice_channels, name="DOTA")
        mock_get.assert_any_call(ctx.guild.text_channels, name="timer-bot")

        # Ensure the message was sent
        mock_text_channel.send.assert_awaited_once_with("Starting regular game timer with countdown '10:00'.")

        # Ensure the timer start was awaited
        mock_timer.start.assert_awaited_once_with(mock_text_channel, "10:00")

@pytest.mark.asyncio
async def test_start_command_invalid_countdown(test_bot, ctx):
    """Test the !start command with invalid countdown format."""
    with patch('discord.ext.commands.Bot.load_extension', new=AsyncMock()):
        # Invoke the command with invalid countdown
        await test_bot.get_command('start')(ctx, "invalid")

        # Assert that an error message is sent
        ctx.send.assert_awaited_once_with("Please enter a valid countdown format (MM:SS or signed integer in seconds).")

@pytest.mark.asyncio
async def test_start_command_already_running(test_bot, ctx):
    """Test the !start command when a timer is already running."""
    with patch('src.bot.GameTimer') as MockGameTimer, \
            patch('discord.utils.get', return_value=AsyncMock()) as mock_get, \
            patch('discord.ext.commands.Bot.load_extension', new=AsyncMock()):
        # Mock the Timer as already running
        mock_timer = Mock()
        mock_timer.is_running.return_value = True
        MockGameTimer.return_value = mock_timer

        # Mock return values for `get`
        mock_voice_channel = AsyncMock()
        mock_text_channel = AsyncMock()
        mock_get.side_effect = [mock_voice_channel, mock_text_channel]

        # Invoke the command
        command = test_bot.get_command('start')
        assert command is not None, "The 'start' command was not registered."
        await command(ctx, "10:00")

        # Assert that an error message is sent
        ctx.send.assert_awaited_once_with("A game timer is already running in this server.")

@pytest.mark.asyncio
async def test_start_timers_in_different_servers():
    """Test starting timers in different servers."""
    from src.bot import game_timers, start_game, VOICE_CHANNEL_NAME, TIMER_CHANNEL_NAME

    # Reset game_timers before the test to ensure isolation
    game_timers.clear()

    # Initialize bot and add the start_game command
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    bot.add_command(start_game)

    # Create mock contexts for two different servers
    ctx_server_a = AsyncMock()
    ctx_server_a.guild.id = 1
    ctx_server_a.guild.name = "Server A"
    ctx_server_a.channel.name = TIMER_CHANNEL_NAME
    ctx_server_a.send = AsyncMock()
    ctx_server_a.author = Mock()
    ctx_server_a.author.guild_permissions = Mock(administrator=True)

    ctx_server_b = AsyncMock()
    ctx_server_b.guild.id = 2
    ctx_server_b.guild.name = "Server B"
    ctx_server_b.channel.name = TIMER_CHANNEL_NAME
    ctx_server_b.send = AsyncMock()
    ctx_server_b.author = Mock()
    ctx_server_b.author.guild_permissions = Mock(administrator=True)

    with patch('src.bot.GameTimer') as MockGameTimer, \
         patch('discord.utils.get') as mock_get, \
         patch('discord.ext.commands.Bot.load_extension', new=AsyncMock()):

        # Create separate AsyncMocks for GameTimer instances in each server
        mock_timer_a = AsyncMock()
        mock_timer_a.is_running.return_value = False

        mock_timer_b = AsyncMock()
        mock_timer_b.is_running.return_value = False

        # Set the side_effect to return different GameTimer instances for each server
        MockGameTimer.side_effect = [mock_timer_a, mock_timer_b]

        # Create AsyncMocks for voice and text channels for both servers
        mock_voice_channel_a = AsyncMock()
        mock_voice_channel_a.name = VOICE_CHANNEL_NAME

        mock_text_channel_a = AsyncMock()
        mock_text_channel_a.name = TIMER_CHANNEL_NAME

        mock_voice_channel_b = AsyncMock()
        mock_voice_channel_b.name = VOICE_CHANNEL_NAME

        mock_text_channel_b = AsyncMock()
        mock_text_channel_b.name = TIMER_CHANNEL_NAME

        # Define the side_effect for discord.utils.get to handle all necessary calls
        # Each start_game call makes 3 calls to discord.utils.get:
        # 1. Get voice channel
        # 2. Get text channel
        # 3. Get voice client
        mock_get.side_effect = [
            mock_voice_channel_a,  # Server A: Get voice channel
            mock_text_channel_a,   # Server A: Get text channel
            None,                  # Server A: Get voice client (None means not connected)
            mock_voice_channel_b,  # Server B: Get voice channel
            mock_text_channel_b,   # Server B: Get text channel
            None                   # Server B: Get voice client (None means not connected)
        ]

        # Start timer in Server A
        command = bot.get_command('start')
        assert command is not None, "The 'start' command was not registered."
        await command(ctx_server_a, "10:00", "regular")

        # Assertions for Server A
        assert ctx_server_a.guild.id in game_timers, "Timer for Server A was not added to game_timers."
        mock_text_channel_a.send.assert_awaited_once_with("Starting regular game timer with countdown '10:00'.")
        mock_timer_a.start.assert_awaited_once_with(mock_text_channel_a, "10:00")

        # Start timer in Server B
        await command(ctx_server_b, "15:00", "turbo")

        # Assertions for Server B
        assert ctx_server_b.guild.id in game_timers, "Timer for Server B was not added to game_timers."
        mock_text_channel_b.send.assert_awaited_once_with("Starting turbo game timer with countdown '15:00'.")
        mock_timer_b.start.assert_awaited_once_with(mock_text_channel_b, "15:00")

        # Ensure both timers are present in game_timers
        assert len(game_timers) == 2, "Timers for both servers were not added to game_timers."
        assert game_timers[1] == mock_timer_a, "Timer for Server A does not match the mock."
        assert game_timers[2] == mock_timer_b, "Timer for Server B does not match the mock."