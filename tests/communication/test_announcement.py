# tests/communication/test_announcement.py
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.communication.announcement import Announcement


@pytest.fixture
def announcement():
    """Instantiate the Announcement class with mocked dependencies."""
    with patch('src.communication.announcement.TTSManager') as MockTTSManager:
        mock_tts_manager = MockTTSManager.return_value
        return Announcement()


@pytest.fixture
def game_timer():
    """Create a mock GameTimer instance."""
    mock_game_timer = Mock()
    mock_game_timer.channel = Mock()
    mock_game_timer.channel.send = AsyncMock()
    mock_game_timer.voice_client = Mock()
    mock_game_timer.voice_client.is_connected.return_value = True
    return mock_game_timer


@pytest.mark.asyncio
async def test_announce_text_channel_success(announcement, game_timer):
    """Test successful announcement in text channel."""
    mock_embed = Mock()
    with patch('discord.Embed', return_value=mock_embed):
        await announcement.announce(game_timer, "Test Message")

        # Check that Embed was created and sent
        game_timer.channel.send.assert_awaited_once_with(embed=mock_embed)


def test_announce_no_text_channel(announcement):
    """Test announcement when text channel is not set."""
    mock_game_timer = Mock()
    mock_game_timer.channel = None

    with patch('discord.Embed') as MockEmbed:
        MockEmbed.return_value = Mock()

        with patch('src.communication.announcement.logger') as mock_logger:
            asyncio.run(announcement.announce(mock_game_timer, "Test Message"))
            mock_logger.warning.assert_called_with("Cannot send message; text channel is not set.")


@pytest.mark.asyncio
async def test_announce_voice_channel_success(announcement, game_timer):
    """Test successful announcement in voice channel."""
    with patch.object(announcement.tts_manager, 'play_tts', new_callable=AsyncMock) as mock_play_tts:
        await announcement.announce(game_timer, "Test Voice Message")
        mock_play_tts.assert_awaited_once_with(game_timer.voice_client, "Test Voice Message")


@pytest.mark.asyncio
async def test_announce_voice_channel_not_connected(announcement, game_timer):
    """Test announcement when voice client is not connected."""
    game_timer.voice_client.is_connected.return_value = False
    with patch('src.communication.announcement.logger') as mock_logger:
        await announcement.announce(game_timer, "Test Voice Message")
        mock_logger.warning.assert_called_with("Voice client is not connected; cannot announce message.")


@pytest.mark.asyncio
async def test_announce_error_sending_text(announcement, game_timer):
    """Test error handling when sending to text channel fails."""
    game_timer.channel.send.side_effect = Exception("Send failed")

    with patch('discord.Embed') as MockEmbed, \
            patch('src.communication.announcement.logger') as mock_logger:
        MockEmbed.return_value = Mock()
        await announcement.announce(game_timer, "Test Message")
        mock_logger.error.assert_called()
