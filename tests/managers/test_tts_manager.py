# tests/managers/test_tts_manager.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import os
import hashlib
import asyncio

from src.managers.tts_manager import TTSManager
from src.utils.config import TTS_CACHE_DIR


@pytest.fixture
def tts_manager():
    return TTSManager()


@pytest.fixture
def mock_voice_client():
    mock = MagicMock()
    mock.is_connected.return_value = True
    mock.is_playing.return_value = False
    mock.play = MagicMock()
    return mock


@pytest.fixture
def mock_message():
    return "Hello, this is a test message for TTS."


@pytest.mark.asyncio
async def test_set_voice(tts_manager):
    """Test that set_voice correctly updates the voice attribute."""
    new_voice = "en-US-AriaNeural"
    await tts_manager.set_voice(new_voice)
    assert tts_manager.voice == new_voice


@pytest.mark.asyncio
async def test_set_voice_logging(tts_manager):
    """Test that set_voice logs the voice change."""
    new_voice = "en-US-JennyNeural"
    with patch('src.utils.config.logger.info') as mock_logger_info:
        await tts_manager.set_voice(new_voice)
        mock_logger_info.assert_called_once_with(f"TTS voice set to {new_voice}")


@pytest.mark.asyncio
async def test_get_tts_audio_with_existing_cache(tts_manager, mock_message):
    """Test that get_tts_audio retrieves audio from cache if it exists."""
    # Generate expected filename
    clean_message = "Hello this is a test message for TTS"
    expected_filename = os.path.join(TTS_CACHE_DIR, f"{hashlib.md5(clean_message.encode()).hexdigest()}.mp3")

    # Mock os.path.exists to return True
    with patch('os.path.exists', return_value=True) as mock_exists, \
            patch('src.utils.config.logger.info') as mock_logger_info:
        audio_file = await tts_manager.get_tts_audio(mock_message)
        mock_exists.assert_called_once_with(expected_filename)
        mock_logger_info.assert_called_once_with(f"Using cached TTS audio for message: '{clean_message}'")
        assert audio_file == expected_filename


@pytest.mark.asyncio
async def test_get_tts_audio_without_existing_cache(tts_manager, mock_message):
    """Test that get_tts_audio generates and saves audio when not cached."""
    clean_message = "Hello this is a test message for TTS"
    expected_filename = os.path.join(TTS_CACHE_DIR, f"{hashlib.md5(clean_message.encode()).hexdigest()}.mp3")

    # Mock os.path.exists to return False initially, then True after generation
    with patch('os.path.exists', side_effect=[False, True]) as mock_exists, \
            patch('edge_tts.Communicate') as mock_communicate_cls, \
            patch('src.utils.config.logger.info') as mock_logger_info:
        # Mock the Communicate instance and its save method
        mock_communicate_instance = MagicMock()
        mock_communicate_instance.save = AsyncMock()
        mock_communicate_cls.return_value = mock_communicate_instance

        audio_file = await tts_manager.get_tts_audio(mock_message)

        # Verify os.path.exists called correctly
        mock_exists.assert_any_call(expected_filename)

        # Verify Communicate was instantiated correctly
        mock_communicate_cls.assert_called_once_with(text=clean_message, voice=tts_manager.voice)

        # Verify save was called with the correct filename
        mock_communicate_instance.save.assert_awaited_once_with(expected_filename)

        # Verify logging
        mock_logger_info.assert_any_call(f"Generating TTS audio for new message: '{clean_message}'")
        mock_logger_info.assert_any_call(f"Saved TTS audio to {expected_filename}")

        assert audio_file == expected_filename


@pytest.mark.asyncio
async def test_get_tts_audio_empty_message(tts_manager):
    """Test that get_tts_audio returns None and logs a warning when the message is empty after cleaning."""
    empty_message = "!!! ???"

    with patch('src.utils.config.logger.warning') as mock_logger_warning:
        audio_file = await tts_manager.get_tts_audio(empty_message)
        mock_logger_warning.assert_called_once_with("Cleaned message is empty. Skipping TTS generation.")
        assert audio_file is None


@pytest.mark.asyncio
async def test_get_tts_audio_exception(tts_manager, mock_message):
    """Test that get_tts_audio handles exceptions during TTS generation."""
    clean_message = "Hello this is a test message for TTS"
    expected_filename = os.path.join(TTS_CACHE_DIR, f"{hashlib.md5(clean_message.encode()).hexdigest()}.mp3")

    with patch('os.path.exists', return_value=False), \
            patch('edge_tts.Communicate', side_effect=Exception("TTS generation failed")), \
            patch('src.utils.config.logger.error') as mock_logger_error:
        audio_file = await tts_manager.get_tts_audio(mock_message)

        # Verify logging
        mock_logger_error.assert_called_once_with("Error generating TTS audio: TTS generation failed", exc_info=True)

        assert audio_file is None


@pytest.mark.asyncio
async def test_play_tts_with_existing_audio(tts_manager, mock_voice_client, mock_message):
    """Test that play_tts plays audio when voice client is connected and not playing."""
    # Generate expected filename
    clean_message = "Hello this is a test message for TTS"
    expected_filename = os.path.join(TTS_CACHE_DIR, f"{hashlib.md5(clean_message.encode()).hexdigest()}.mp3")

    # Mock get_tts_audio to return the expected filename
    with patch.object(tts_manager, 'get_tts_audio', return_value=expected_filename) as mock_get_tts_audio, \
            patch('discord.FFmpegPCMAudio') as mock_ffmpeg, \
            patch('discord.PCMVolumeTransformer') as mock_pcm_volume, \
            patch('src.utils.config.logger.info') as mock_logger_info, \
            patch('src.utils.config.logger.warning') as mock_logger_warning:
        # Mock FFmpegPCMAudio and PCMVolumeTransformer
        mock_audio_source = MagicMock()
        mock_ffmpeg.return_value = mock_audio_source
        mock_volume_transformer = MagicMock()
        mock_pcm_volume.return_value = mock_volume_transformer

        # Mock is_playing to return False initially, then True to simulate playing
        mock_voice_client.is_playing.side_effect = [False, True, False]

        # Run play_tts
        play_task = asyncio.create_task(tts_manager.play_tts(mock_voice_client, mock_message))

        # Allow some time for the while loop to execute
        await asyncio.sleep(0.2)

        # Stop the task to prevent it from waiting indefinitely
        play_task.cancel()

        # Verify get_tts_audio was called
        mock_get_tts_audio.assert_awaited_once_with(mock_message)

        # Verify FFmpegPCMAudio was instantiated correctly
        mock_ffmpeg.assert_called_once_with(expected_filename)

        # Verify PCMVolumeTransformer was instantiated with correct volume
        mock_pcm_volume.assert_called_once_with(mock_audio_source, volume=tts_manager.volume)

        # Verify that voice_client.play was called with the volume-controlled audio and any 'after' callable
        mock_voice_client.play.assert_called_once_with(mock_volume_transformer, after=ANY)

        # Verify logging
        mock_logger_info.assert_any_call(
            f"Started playing audio in voice channel for message: '{mock_message}' with volume={tts_manager.volume}")


@pytest.mark.asyncio
async def test_play_tts_already_playing(tts_manager, mock_voice_client, mock_message):
    """Test that play_tts does not play audio if the voice client is already playing."""
    # Mock get_tts_audio to return a filename
    with patch.object(tts_manager, 'get_tts_audio', return_value="fake_audio.mp3") as mock_get_tts_audio, \
            patch('discord.FFmpegPCMAudio'), \
            patch('discord.PCMVolumeTransformer'), \
            patch('src.utils.config.logger.warning') as mock_logger_warning:
        # Mock is_playing to return True
        mock_voice_client.is_playing.return_value = True

        await tts_manager.play_tts(mock_voice_client, mock_message)

        # Verify that play was not called since already playing
        mock_get_tts_audio.assert_awaited_once_with(mock_message)
        mock_logger_warning.assert_called_once_with("Voice client is already playing audio.")


@pytest.mark.asyncio
async def test_play_tts_no_audio(tts_manager, mock_voice_client, mock_message):
    """Test that play_tts does not attempt to play audio if audio_file is None."""
    # Mock get_tts_audio to return None
    with patch.object(tts_manager, 'get_tts_audio', return_value=None) as mock_get_tts_audio, \
            patch('src.utils.config.logger.warning') as mock_logger_warning:
        await tts_manager.play_tts(mock_voice_client, mock_message)

        # Verify that play was not called
        mock_get_tts_audio.assert_awaited_once_with(mock_message)
        mock_logger_warning.assert_called_once_with(
            "Voice client is not connected or TTS audio could not be generated.")


@pytest.mark.asyncio
async def test_play_tts_voice_client_not_connected(tts_manager, mock_voice_client, mock_message):
    """Test that play_tts does not attempt to play audio if voice client is not connected."""
    # Mock get_tts_audio to return a filename
    with patch.object(tts_manager, 'get_tts_audio', return_value="fake_audio.mp3") as mock_get_tts_audio, \
            patch('discord.FFmpegPCMAudio'), \
            patch('discord.PCMVolumeTransformer'), \
            patch('src.utils.config.logger.warning') as mock_logger_warning:
        # Mock is_connected to return False
        mock_voice_client.is_connected.return_value = False

        await tts_manager.play_tts(mock_voice_client, mock_message)

        # Verify that play was not called
        mock_get_tts_audio.assert_awaited_once_with(mock_message)
        mock_logger_warning.assert_called_once_with(
            "Voice client is not connected or TTS audio could not be generated.")


@pytest.mark.asyncio
async def test_set_volume_valid(tts_manager):
    """Test that set_volume correctly updates the volume when given a valid value."""
    new_volume = 0.8
    with patch('src.utils.config.logger.info') as mock_logger_info:
        await tts_manager.set_volume(new_volume)
        assert tts_manager.volume == new_volume
        mock_logger_info.assert_called_once_with(f"Volume set to {tts_manager.volume}")


@pytest.mark.asyncio
async def test_set_volume_invalid_low(tts_manager):
    """Test that set_volume does not update the volume and logs a warning when given a value below 0.0."""
    invalid_volume = -0.1
    with patch('src.utils.config.logger.warning') as mock_logger_warning:
        await tts_manager.set_volume(invalid_volume)
        assert tts_manager.volume == 0.5  # Default volume
        mock_logger_warning.assert_called_once_with("Invalid volume level. Volume must be between 0.0 and 1.0.")


@pytest.mark.asyncio
async def test_set_volume_invalid_high(tts_manager):
    """Test that set_volume does not update the volume and logs a warning when given a value above 1.0."""
    invalid_volume = 1.1
    with patch('src.utils.config.logger.warning') as mock_logger_warning:
        await tts_manager.set_volume(invalid_volume)
        assert tts_manager.volume == 0.5  # Default volume
        mock_logger_warning.assert_called_once_with("Invalid volume level. Volume must be between 0.0 and 1.0.")
