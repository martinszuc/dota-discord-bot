# tests/communication/test_announcement.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.communication.announcement import Announcement
from src.managers.tts_manager import TTSManager

# Assuming GameTimer is a class used within Announcement
# If GameTimer is part of your project, import it accordingly
# For example:
# from src.timers.game_timer import GameTimer

# Mock GameTimer for testing purposes
class MockGameTimer:
    def __init__(self, guild_id, channel=None, voice_client=None):
        self.guild_id = guild_id
        self.channel = channel
        self.voice_client = voice_client

@pytest.fixture
def mock_game_timer():
    return MagicMock()

@pytest.fixture
def announcement():
    return Announcement()

@pytest.mark.asyncio
async def test_announce_with_valid_channels(announcement, mock_game_timer):
    """Test that announce sends messages to both text and voice channels when available."""
    # Setup mock channel and voice_client
    mock_channel = MagicMock()
    mock_voice_client = MagicMock()
    mock_voice_client.is_connected.return_value = True

    mock_game_timer.channel = mock_channel
    mock_game_timer.voice_client = mock_voice_client

    message = "Test announcement message."

    with patch.object(TTSManager, 'play_tts', new=AsyncMock()) as mock_play_tts:
        await announcement.announce(mock_game_timer, message)

        # Verify that a message was sent to the text channel
        mock_channel.send.assert_awaited_once()
        sent_embed = mock_channel.send.await_args[0][0]
        assert sent_embed.description == message
        assert sent_embed.color == 0x00ff00

        # Verify that play_tts was called
        mock_play_tts.assert_awaited_once_with(mock_voice_client, message)

@pytest.mark.asyncio
async def test_announce_without_text_channel(announcement, mock_game_timer):
    """Test that announce logs a warning and does not attempt to send a text message when text channel is None."""
    mock_game_timer.channel = None
    mock_voice_client = MagicMock()
    mock_voice_client.is_connected.return_value = True
    mock_game_timer.voice_client = mock_voice_client

    message = "Test announcement without text channel."

    with patch.object(TTSManager, 'play_tts', new=AsyncMock()) as mock_play_tts, \
         patch('src.utils.config.logger.warning') as mock_logger_warning:
        await announcement.announce(mock_game_timer, message)

        # Verify that no message was sent to the text channel
        # Since channel is None, send should not be called
        # Hence, no need to check mock_channel.send

        # Verify that a warning was logged
        mock_logger_warning.assert_called_once_with("Cannot send message; text channel is not set.")

        # Verify that play_tts was called
        mock_play_tts.assert_awaited_once_with(mock_voice_client, message)

@pytest.mark.asyncio
async def test_announce_without_voice_client(announcement, mock_game_timer):
    """Test that announce logs a warning and does not attempt to play TTS when voice_client is None."""
    mock_channel = MagicMock()
    mock_game_timer.channel = mock_channel
    mock_game_timer.voice_client = None

    message = "Test announcement without voice client."

    with patch.object(TTSManager, 'play_tts', new=AsyncMock()) as mock_play_tts, \
         patch('src.utils.config.logger.warning') as mock_logger_warning:
        await announcement.announce(mock_game_timer, message)

        # Verify that a message was sent to the text channel
        mock_channel.send.assert_awaited_once()
        sent_embed = mock_channel.send.await_args[0][0]
        assert sent_embed.description == message
        assert sent_embed.color == 0x00ff00

        # Verify that play_tts was not called
        mock_play_tts.assert_not_called()

        # Verify that a warning was logged
        mock_logger_warning.assert_called_once_with("Voice client is not connected; cannot announce message.")

@pytest.mark.asyncio
async def test_announce_voice_client_not_connected(announcement, mock_game_timer):
    """Test that announce logs a warning and does not attempt to play TTS when voice_client is not connected."""
    mock_channel = MagicMock()
    mock_voice_client = MagicMock()
    mock_voice_client.is_connected.return_value = False

    mock_game_timer.channel = mock_channel
    mock_game_timer.voice_client = mock_voice_client

    message = "Test announcement with disconnected voice client."

    with patch.object(TTSManager, 'play_tts', new=AsyncMock()) as mock_play_tts, \
         patch('src.utils.config.logger.warning') as mock_logger_warning:
        await announcement.announce(mock_game_timer, message)

        # Verify that a message was sent to the text channel
        mock_channel.send.assert_awaited_once()
        sent_embed = mock_channel.send.await_args[0][0]
        assert sent_embed.description == message
        assert sent_embed.color == 0x00ff00

        # Verify that play_tts was not called
        mock_play_tts.assert_not_called()

        # Verify that a warning was logged
        mock_logger_warning.assert_called_once_with("Voice client is not connected; cannot announce message.")

@pytest.mark.asyncio
async def test_announce_tts_exception_handling(announcement, mock_game_timer):
    """Test that announce handles exceptions raised by play_tts gracefully."""
    mock_channel = MagicMock()
    mock_voice_client = MagicMock()
    mock_voice_client.is_connected.return_value = True

    mock_game_timer.channel = mock_channel
    mock_game_timer.voice_client = mock_voice_client

    message = "Test announcement with TTS exception."

    with patch.object(TTSManager, 'play_tts', new=AsyncMock(side_effect=Exception("TTS error"))) as mock_play_tts, \
         patch('src.utils.config.logger.error') as mock_logger_error:
        await announcement.announce(mock_game_timer, message)

        # Verify that a message was sent to the text channel
        mock_channel.send.assert_awaited_once()
        sent_embed = mock_channel.send.await_args[0][0]
        assert sent_embed.description == message
        assert sent_embed.color == 0x00ff00

        # Verify that play_tts was called
        mock_play_tts.assert_awaited_once_with(mock_voice_client, message)

        # Verify that an error was logged
        mock_logger_error.assert_called_once()
