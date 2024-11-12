# tests/src/managers/test_event_manager.py

import pytest
from unittest.mock import MagicMock, patch
from src.managers.event_manager import EventsManager
from src.database import StaticEvent, PeriodicEvent, ServerSettings
from src.event_definitions import (
    regular_static_events,
    regular_periodic_events,
    turbo_static_events,
    turbo_periodic_events,
)

@pytest.mark.usefixtures("events_manager")
class TestEventsManager:
    def test_guild_has_events_with_no_events(self, events_manager, mock_session):
        """Test guild_has_events returns False when there are no events."""
        # Setup the mock to return None for both queries
        mock_session.query().filter_by().first.return_value = None

        guild_id = 123456789
        assert not events_manager.guild_has_events(guild_id)
        mock_session.query().filter_by.assert_any_call(guild_id=str(guild_id))

    def test_guild_has_events_with_static_events(self, events_manager, mock_session):
        """Test guild_has_events returns True when there are static events."""
        # Setup the mock to return a StaticEvent
        mock_static_event = MagicMock(spec=StaticEvent)
        mock_session.query().filter_by().first.side_effect = [mock_static_event, None]

        guild_id = 123456789
        assert events_manager.guild_has_events(guild_id)
        # Verify that queries were made
        mock_session.query().filter_by.assert_any_call(guild_id=str(guild_id))

    def test_guild_has_events_with_periodic_events(self, events_manager, mock_session):
        """Test guild_has_events returns True when there are periodic events."""
        # Setup the mock to return None for static events and a PeriodicEvent
        mock_periodic_event = MagicMock(spec=PeriodicEvent)
        mock_session.query().filter_by().first.side_effect = [None, mock_periodic_event]

        guild_id = 123456789
        assert events_manager.guild_has_events(guild_id)
        # Verify that queries were made
        mock_session.query().filter_by.assert_any_call(guild_id=str(guild_id))

    def test_populate_events_for_guild(self, events_manager, mock_session):
        """Test populate_events_for_guild correctly adds events."""
        guild_id = 123456789

        # Mock the StaticEvent and PeriodicEvent constructors
        with patch('src.managers.event_manager.StaticEvent') as MockStaticEvent, \
             patch('src.managers.event_manager.PeriodicEvent') as MockPeriodicEvent:

            # Populate events
            events_manager.populate_events_for_guild(guild_id)

            # Verify StaticEvent was called correctly
            assert MockStaticEvent.call_count == len(regular_static_events) + len(turbo_static_events)
            # Verify PeriodicEvent was called correctly
            assert MockPeriodicEvent.call_count == len(regular_periodic_events) + len(turbo_periodic_events)

            # Ensure session.add was called for each event
            assert mock_session.add.call_count == (
                len(regular_static_events) + len(turbo_static_events) +
                len(regular_periodic_events) + len(turbo_periodic_events)
            )
            # Verify commit was called
            mock_session.commit.assert_called_once()

    def test_get_static_events(self, events_manager, mock_session):
        """Test get_static_events retrieves the correct events."""
        guild_id = 123456789
        mode = 'regular'

        # Create mock StaticEvents
        mock_static_event1 = MagicMock(spec=StaticEvent, id=1, time=300, message="First Event")
        mock_static_event2 = MagicMock(spec=StaticEvent, id=2, time=600, message="Second Event")

        mock_session.query().filter_by().all.return_value = [mock_static_event1, mock_static_event2]

        events = events_manager.get_static_events(guild_id, mode)

        # Verify the returned dictionary
        expected = {
            1: {"time": 300, "message": "First Event"},
            2: {"time": 600, "message": "Second Event"},
        }
        assert events == expected

        # Verify that the query was made with correct parameters
        mock_session.query().filter_by.assert_called_with(guild_id=str(guild_id), mode=mode)

    def test_get_periodic_events(self, events_manager, mock_session):
        """Test get_periodic_events retrieves the correct events."""
        guild_id = 123456789
        mode = 'regular'

        # Create mock PeriodicEvents
        mock_periodic_event1 = MagicMock(spec=PeriodicEvent, id=1, start_time=100, interval=50, end_time=300, message="Periodic Event 1")
        mock_periodic_event2 = MagicMock(spec=PeriodicEvent, id=2, start_time=200, interval=60, end_time=400, message="Periodic Event 2")

        mock_session.query().filter_by().all.return_value = [mock_periodic_event1, mock_periodic_event2]

        events = events_manager.get_periodic_events(guild_id, mode)

        # Verify the returned dictionary
        expected = {
            1: {"start_time": 100, "interval": 50, "end_time": 300, "message": "Periodic Event 1"},
            2: {"start_time": 200, "interval": 60, "end_time": 400, "message": "Periodic Event 2"},
        }
        assert events == expected

        # Verify that the query was made with correct parameters
        mock_session.query().filter_by.assert_called_with(guild_id=str(guild_id), mode=mode)

    def test_add_static_event(self, events_manager, mock_session):
        """Test add_static_event adds a static event correctly."""
        guild_id = 123456789
        time = 600
        message = "New Static Event"
        mode = 'regular'

        # Mock the StaticEvent constructor and its ID
        with patch('src.managers.event_manager.StaticEvent', autospec=True) as MockStaticEvent:
            mock_event_instance = MagicMock(spec=StaticEvent)
            mock_event_instance.id = 10
            MockStaticEvent.return_value = mock_event_instance

            event_id = events_manager.add_static_event(guild_id, time, message, mode)

            # Verify that StaticEvent was instantiated correctly
            MockStaticEvent.assert_called_once_with(
                guild_id=str(guild_id),
                mode=mode,
                time=time,
                message=message
            )
            # Verify that session.add was called with the event
            mock_session.add.assert_called_once_with(mock_event_instance)
            # Verify that commit was called
            mock_session.commit.assert_called_once()

            # Verify the returned event ID
            assert event_id == 10

    def test_add_periodic_event(self, events_manager, mock_session):
        """Test add_periodic_event adds a periodic event correctly."""
        guild_id = 123456789
        start_time = 100
        interval = 50
        end_time = 300
        message = "New Periodic Event"
        mode = 'regular'

        # Mock the PeriodicEvent constructor and its ID
        with patch('src.managers.event_manager.PeriodicEvent', autospec=True) as MockPeriodicEvent:
            mock_event_instance = MagicMock(spec=PeriodicEvent)
            mock_event_instance.id = 20
            MockPeriodicEvent.return_value = mock_event_instance

            event_id = events_manager.add_periodic_event(guild_id, start_time, interval, end_time, message, mode)

            # Verify that PeriodicEvent was instantiated correctly
            MockPeriodicEvent.assert_called_once_with(
                guild_id=str(guild_id),
                mode=mode,
                start_time=start_time,
                interval=interval,
                end_time=end_time,
                message=message
            )
            # Verify that session.add was called with the event
            mock_session.add.assert_called_once_with(mock_event_instance)
            # Verify that commit was called
            mock_session.commit.assert_called_once()

            # Verify the returned event ID
            assert event_id == 20

    def test_remove_event_static(self, events_manager, mock_session):
        """Test remove_event successfully removes a static event."""
        guild_id = 123456789
        event_id = 1

        # Mock a StaticEvent
        mock_static_event = MagicMock(spec=StaticEvent)
        mock_session.query().filter_by().first.return_value = mock_static_event

        result = events_manager.remove_event(guild_id, event_id)

        # Verify that the event was deleted
        mock_session.delete.assert_called_once_with(mock_static_event)
        # Verify that commit was called
        mock_session.commit.assert_called_once()
        # Verify the result
        assert result is True

    def test_remove_event_periodic(self, events_manager, mock_session):
        """Test remove_event successfully removes a periodic event."""
        guild_id = 123456789
        event_id = 2

        # Mock a PeriodicEvent
        mock_periodic_event = MagicMock(spec=PeriodicEvent)
        mock_session.query().filter_by().first.side_effect = [None, mock_periodic_event]

        result = events_manager.remove_event(guild_id, event_id)

        # Verify that the event was deleted
        mock_session.delete.assert_called_once_with(mock_periodic_event)
        # Verify that commit was called
        mock_session.commit.assert_called_once()
        # Verify the result
        assert result is True

    def test_remove_event_not_found(self, events_manager, mock_session):
        """Test remove_event returns False when the event is not found."""
        guild_id = 123456789
        event_id = 999

        # Mock no event found
        mock_session.query().filter_by().first.return_value = None

        result = events_manager.remove_event(guild_id, event_id)

        # Verify that delete was not called
        mock_session.delete.assert_not_called()
        # Verify that commit was not called
        mock_session.commit.assert_not_called()
        # Verify the result
        assert result is False

    def test_set_mindful_messages_enable(self, events_manager, mock_session):
        """Test set_mindful_messages enables mindful messages."""
        guild_id = 123456789

        # Mock existing ServerSettings
        mock_settings = MagicMock(spec=ServerSettings)
        mock_session.query().filter_by().first.return_value = mock_settings

        events_manager.set_mindful_messages(guild_id, True)

        # Verify that mindful_messages_enabled was set to 1
        mock_settings.mindful_messages_enabled = 1
        # Verify that commit was called
        mock_session.commit.assert_called_once()

    def test_set_mindful_messages_disable(self, events_manager, mock_session):
        """Test set_mindful_messages disables mindful messages."""
        guild_id = 123456789

        # Mock existing ServerSettings
        mock_settings = MagicMock(spec=ServerSettings)
        mock_session.query().filter_by().first.return_value = mock_settings

        events_manager.set_mindful_messages(guild_id, False)

        # Verify that mindful_messages_enabled was set to 0
        mock_settings.mindful_messages_enabled = 0
        # Verify that commit was called
        mock_session.commit.assert_called_once()

    def test_set_mindful_messages_create_new(self, events_manager, mock_session):
        """Test set_mindful_messages creates new ServerSettings if none exist."""
        guild_id = 123456789

        # Mock no existing ServerSettings
        mock_session.query().filter_by().first.return_value = None

        with patch('src.managers.event_manager.ServerSettings') as MockServerSettings:
            mock_new_settings = MagicMock(spec=ServerSettings)
            MockServerSettings.return_value = mock_new_settings

            events_manager.set_mindful_messages(guild_id, True)

            # Verify that ServerSettings was instantiated correctly
            MockServerSettings.assert_called_once_with(server_id=str(guild_id), mindful_messages_enabled=1)
            # Verify that session.add was called with new settings
            mock_session.add.assert_called_once_with(mock_new_settings)
            # Verify that commit was called
            mock_session.commit.assert_called_once()

    def test_mindful_messages_enabled_true(self, events_manager, mock_session):
        """Test mindful_messages_enabled returns True when enabled."""
        guild_id = 123456789

        mock_settings = MagicMock(spec=ServerSettings)
        mock_settings.mindful_messages_enabled = 1
        mock_session.query().filter_by().first.return_value = mock_settings

        assert events_manager.mindful_messages_enabled(guild_id) == True

    def test_mindful_messages_enabled_false(self, events_manager, mock_session):
        """Test mindful_messages_enabled returns False when disabled."""
        guild_id = 123456789

        mock_settings = MagicMock(spec=ServerSettings)
        mock_settings.mindful_messages_enabled = 0
        mock_session.query().filter_by().first.return_value = mock_settings

        assert events_manager.mindful_messages_enabled(guild_id) == False

    def test_mindful_messages_enabled_no_settings(self, events_manager, mock_session):
        """Test mindful_messages_enabled returns False when no settings exist."""
        guild_id = 123456789

        mock_session.query().filter_by().first.return_value = None

        assert events_manager.mindful_messages_enabled(guild_id) == False
