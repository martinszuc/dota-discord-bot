import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.communication.announcement import Announcement


@pytest.fixture
def announcement():
    with patch('src.communication.announcement.TTSManager') as MockTTSManager:
        mock_tts_manager = MockTTSManager.return_value
        ann = Announcement()
        # Mock play_tts to track calls
        ann.tts_manager.play_tts = AsyncMock()
        return ann

@pytest.fixture
def game_timer():
    mock_game_timer = Mock()
    mock_game_timer.channel = Mock()
    mock_game_timer.channel.send = AsyncMock()
    mock_game_timer.voice_client = Mock()
    mock_game_timer.voice_client.is_connected.return_value = True
    return mock_game_timer

@pytest.mark.asyncio
async def test_announcement_queue(announcement, game_timer):
    """Test that multiple messages are queued and played in order."""
    # Send multiple messages at the same time
    await announcement.announce(game_timer, "Message 1")
    await announcement.announce(game_timer, "Message 2")
    await announcement.announce(game_timer, "Message 3")

    # Give some time for the consumer to process
    await asyncio.sleep(0.2)  # Increased wait time

    # Ensure the announcement method was called for each message
    announcement.tts_manager.play_tts.assert_any_call(game_timer.voice_client, "Message 1")
    announcement.tts_manager.play_tts.assert_any_call(game_timer.voice_client, "Message 2")
    announcement.tts_manager.play_tts.assert_any_call(game_timer.voice_client, "Message 3")

    # Verify multiple messages in the expected order
    calls = announcement.tts_manager.play_tts.await_args_list
    played_messages = [call.args[1] for call in calls]
    assert played_messages == ["Message 1", "Message 2", "Message 3"]