import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.timers.glyph import GlyphTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer
from src.communication.game_status_manager import GameStatusMessageManager


@pytest.mark.asyncio
@pytest.mark.parametrize("TimerClass,mode,expected_messages", [
    (GlyphTimer, "regular", [
        "Enemy glyph activated. Cooldown started.",
        "Enemy glyph is now available!"
    ]),
    (GlyphTimer, "turbo", [
        "Enemy glyph activated. Cooldown started.",
        "Enemy glyph is now available!"
    ]),
    (RoshanTimer, "regular", [
        "Roshan timer started.",
        "Dropped: Aegis",
        f"Next Roshan between minute 8 and 11.",
        "Roshan will spawn at bottom lane.",
        "Roshan may respawn in 5 minutes!",
        "Roshan may respawn in 3 minutes!",
        "Roshan may respawn in 1 minute!",
        "Roshan may be up now!",
        "Roshan is definitely up now!"
    ]),
    (RoshanTimer, "turbo", [
        "Roshan timer started.",
        "Dropped: Aegis",
        f"Next Roshan between minute 4 and 5.",
        "Roshan will spawn at bottom lane.",
        "Roshan may respawn in 5 minutes!",
        "Roshan may respawn in 3 minutes!",
        "Roshan may respawn in 1 minute!",
        "Roshan may be up now!",
        "Roshan is definitely up now!"
    ]),
    (TormentorTimer, "regular", [
        "Tormentor timer started.",
        "Tormentor will respawn in 3 minutes!",
        "Tormentor will respawn in 1 minute!",
        "Tormentor has respawned!"
    ]),
    (TormentorTimer, "turbo", [
        "Tormentor timer started.",
        "Tormentor will respawn in 3 minutes!",
        "Tormentor will respawn in 1 minute!",
        "Tormentor has respawned!"
    ]),
])
async def test_timer_announcements(TimerClass, mode, expected_messages):
    """
    Test timer announcements for different timer types and modes.
    """
    # Create a comprehensive mock game timer
    mock_game_timer = Mock()
    mock_game_timer.mode = mode
    mock_game_timer.time_elapsed = 0
    mock_game_timer.voice_client = Mock()
    mock_game_timer.voice_client.is_connected.return_value = True
    mock_game_timer.channel = Mock()

    # Capture actual messages
    actual_messages = []

    # Create a custom announcement mock that captures messages
    class CustomAnnouncement:
        async def announce(self, game_timer, message):
            actual_messages.append(message)
            return None

    # Create mock channel
    mock_channel = AsyncMock()

    # Instantiate the timer
    timer = TimerClass(game_timer=mock_game_timer)

    # Replace the announcement with our custom mock
    timer.announcement = CustomAnnouncement()

    # Patch sleep methods to prevent actual waiting
    def quick_sleep(duration):
        return asyncio.sleep(0.01)

    with (
        patch.object(timer, 'sleep_with_pause', side_effect=quick_sleep),
        patch.object(timer, '_run_timer', wraps=timer._run_timer)
    ):
        try:
            # Start the timer
            await timer.start(mock_channel)

            # Wait a short time to allow announcements to be generated
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error during timer start: {e}")
            raise
        finally:
            # Always stop the timer
            await timer.stop()

    # Verify messages
    for expected_msg in expected_messages:
        assert any(expected_msg in msg for msg in actual_messages), \
            f"Expected message '{expected_msg}' not found in actual messages"


@pytest.mark.asyncio
async def test_timer_pause_resume():
    """
    Test pause and resume functionality for timers.
    """
    # Test each timer type
    for TimerClass in [GlyphTimer, RoshanTimer, TormentorTimer]:
        # Create a mock game timer
        mock_game_timer = Mock()
        mock_game_timer.mode = 'regular'
        mock_game_timer.time_elapsed = 0
        mock_game_timer.voice_client = Mock()
        mock_game_timer.voice_client.is_connected.return_value = True
        mock_game_timer.channel = Mock()

        # Create mock channel
        mock_channel = AsyncMock()

        # Instantiate the timer
        timer = TimerClass(game_timer=mock_game_timer)

        # Start the timer
        await timer.start(mock_channel)
        assert timer.is_running, f"{TimerClass.__name__} should be running after start"

        # Pause the timer
        await timer.pause()
        assert timer.is_paused, f"{TimerClass.__name__} should be paused"

        # Resume the timer
        await timer.resume()
        assert not timer.is_paused, f"{TimerClass.__name__} should not be paused after resume"

        # Cleanup
        await timer.stop()