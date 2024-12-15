# tests/conftest.py

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add the project root to PYTHONPATH to ensure proper module imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Mock Discord's Context
@pytest.fixture
def mock_ctx():
    mock = MagicMock()
    mock.author.guild_permissions = MagicMock()
    mock.guild.id = 123456789
    mock.guild.name = "TestGuild"
    mock.channel.name = "timer-bot"
    mock.message.content = "!start 10:00"
    mock.send = AsyncMock()
    return mock

# Mock Database Session
@pytest.fixture
def mock_session():
    mock = MagicMock()
    yield mock
    mock.close.assert_called_once()

# Fixture for EventsManager with mocked session
@pytest.fixture
def events_manager(mock_session):
    from src.managers.event_manager import EventsManager
    manager = EventsManager()
    manager.session = mock_session
    yield manager
    manager.close()  # Ensure the close method is called after each test
