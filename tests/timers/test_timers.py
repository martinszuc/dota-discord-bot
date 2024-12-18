import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.communication.game_status_manager import GameStatusMessageManager
from src.timer import GameTimer
from src.timers.glyph import GlyphTimer
from src.timers.roshan import RoshanTimer
from src.timers.tormentor import TormentorTimer


#
# ---------------------
#  TEST: GameTimer
# ---------------------
#

@pytest.mark.asyncio
async def test_game_timer_regular_mode():
    """Test GameTimer in regular mode with negative countdown."""
    mock_channel = AsyncMock()  # Use AsyncMock for mock_channel
    mock_announcement = Mock()

    # Mock status_manager to prevent actual Discord API calls
    with patch.object(GameStatusMessageManager, 'create_status_message', return_value=None), \
         patch.object(GameStatusMessageManager, 'update_status_message', return_value=None):
        game_timer = GameTimer(guild_id=1, mode='regular')
        game_timer.channel = mock_channel
        game_timer.announcement_manager = mock_announcement

        # Start the timer with a negative countdown (means 30s elapsed)
        await game_timer.start(mock_channel, countdown="-30")
        assert game_timer.time_elapsed == 30
        assert game_timer.mode == "regular"
        assert game_timer.is_running()

        # Stop the timer
        with patch.object(game_timer, "_stop_all_child_timers", new_callable=AsyncMock) as stop_child_timers:
            await game_timer.stop()
            # Allow event loop to process cancellations
            await asyncio.sleep(0.1)
            stop_child_timers.assert_called_once()
            assert not game_timer.is_running()


@pytest.mark.asyncio
async def test_game_timer_turbo_mode():
    """Test GameTimer in turbo mode with positive countdown."""
    mock_channel = AsyncMock()  # Use AsyncMock for mock_channel
    mock_announcement = Mock()

    # Mock status_manager to prevent actual Discord API calls
    with patch.object(GameStatusMessageManager, 'create_status_message', return_value=None), \
         patch.object(GameStatusMessageManager, 'update_status_message', return_value=None):
        game_timer = GameTimer(guild_id=2, mode='turbo')
        game_timer.channel = mock_channel
        game_timer.announcement_manager = mock_announcement

        # Start the timer with a positive countdown "10" => time_elapsed = -10
        await game_timer.start(mock_channel, countdown="10")
        assert game_timer.time_elapsed == -10
        assert game_timer.mode == "turbo"
        assert game_timer.is_running()

        with patch.object(game_timer, "_stop_all_child_timers", new_callable=AsyncMock) as stop_child_timers:
            await game_timer.stop()
            # Allow event loop to process cancellations
            await asyncio.sleep(0.1)
            stop_child_timers.assert_called_once()
            assert not game_timer.is_running()


#
# --------------------------------------
#  PARAMETERIZED TESTS: Child Timers
# --------------------------------------
#

@pytest.mark.asyncio
@pytest.mark.parametrize("TimerClass,mode", [
    (GlyphTimer,     "regular"),
    (GlyphTimer,     "turbo"),
    (RoshanTimer,    "regular"),
    (RoshanTimer,    "turbo"),
    (TormentorTimer, "regular"),
    (TormentorTimer, "turbo"),
])
async def test_child_timers_all_modes(TimerClass, mode):
    """
    Test GlyphTimer, RoshanTimer, TormentorTimer in both 'regular' and 'turbo' modes.
    Checks:
      1) Timer can start.
      2) Announcements are correct.
      3) Pause/Resume works.
      4) Timer stops cleanly.
    """
    mock_game_timer = Mock()
    mock_game_timer.mode = mode
    mock_game_timer.time_elapsed = 100  # arbitrary
    mock_announcement = AsyncMock()
    mock_channel = AsyncMock()  # Use AsyncMock for mock_channel

    # Mock status_manager to prevent actual Discord API calls
    with patch.object(GameStatusMessageManager, 'update_status_message', return_value=None):
        timer = TimerClass(game_timer=mock_game_timer)
        timer.announcement = mock_announcement

        # Start the timer
        await timer.start(mock_channel)
        assert timer.is_running

        # Pause the timer
        await timer.pause()
        assert timer.is_paused
        # Resume the timer
        await timer.resume()
        assert not timer.is_paused

        with patch.object(timer, "sleep_with_pause", new_callable=AsyncMock):
            # Mock _run_timer to prevent actual running
            with patch.object(timer, "_run_timer", new_callable=AsyncMock):
                await timer._run_timer(mock_channel)

        # Verify the key announcements
        if TimerClass is RoshanTimer:
            mock_announcement.announce.assert_any_call(mock_game_timer, "Roshan timer started.")
            mock_announcement.announce.assert_any_call(mock_game_timer, "Roshan is definitely up now!")
        elif TimerClass is TormentorTimer:
            mock_announcement.announce.assert_any_call(mock_game_timer, "Tormentor timer started.")
            mock_announcement.announce.assert_any_call(mock_game_timer, "Tormentor has respawned!")
        elif TimerClass is GlyphTimer:
            mock_announcement.announce.assert_any_call(mock_game_timer, "Enemy glyph activated. Cooldown started.")
            mock_announcement.announce.assert_any_call(mock_game_timer, "Enemy glyph is now available!")

        # Stop the timer
        await timer.stop()
        # Give the event loop time to process stop
        await asyncio.sleep(0.1)
        assert not timer.is_running
