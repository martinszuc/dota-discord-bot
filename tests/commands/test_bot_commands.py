# tests/commands/test_bot_commands.py
import discord
import pytest
from unittest.mock import AsyncMock, Mock, patch
from discord.ext import commands
from src.bot import bot  # Adjust the import path as necessary

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

