# src/managers/event_manager.py

import random

from src.utils.config import logger
from sqlalchemy.orm import sessionmaker
from src.database import StaticEvent, PeriodicEvent, engine, ServerSettings
from src.event_definitions import (
    regular_static_events,
    regular_periodic_events,
    turbo_static_events,
    turbo_periodic_events,
    mindful_messages
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.debug("Database session maker created.")

class EventsManager:
    """Class to manage static and periodic events for different game modes."""

    def __init__(self):
        self.session = SessionLocal()
        logger.debug("EventsManager session initialized.")

    def guild_has_events(self, guild_id):
        """Check if a guild already has any events."""
        try:
            has_static = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id)).first() is not None
            has_periodic = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id)).first() is not None
            logger.debug(f"Guild ID {guild_id} has events: Static={has_static}, Periodic={has_periodic}.")
            return has_static or has_periodic
        except Exception as e:
            logger.error(f"Error checking if guild ID {guild_id} has events: {e}", exc_info=True)
            return False

    def populate_events_for_guild(self, guild_id):
        """Populate the database with base events for a specific guild."""
        logger.info(f"Populating events for guild ID {guild_id}.")
        try:
            # Add static events
            for event_data in regular_static_events + turbo_static_events:
                static_event = StaticEvent(
                    guild_id=str(guild_id),
                    mode=event_data['mode'],
                    time=event_data['time'],
                    message=event_data['message']
                )
                self.session.add(static_event)
                logger.debug(f"Added StaticEvent: {static_event}")

            # Add periodic events
            for event_data in regular_periodic_events + turbo_periodic_events:
                periodic_event = PeriodicEvent(
                    guild_id=str(guild_id),
                    mode=event_data['mode'],
                    start_time=event_data['start_time'],
                    interval=event_data['interval'],
                    end_time=event_data['end_time'],
                    message=event_data['message']
                )
                self.session.add(periodic_event)
                logger.debug(f"Added PeriodicEvent: {periodic_event}")

            self.session.commit()
            logger.info(f"Successfully populated events for guild ID {guild_id}.")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error populating events for guild ID {guild_id}: {e}", exc_info=True)

    def get_static_events(self, guild_id, mode='regular'):
        """Retrieve all static events for a guild and mode."""
        try:
            events = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
            event_dict = {event.id: {"time": event.time, "message": event.message} for event in events}
            logger.debug(f"Retrieved {len(event_dict)} static events for guild ID {guild_id} in mode '{mode}'.")
            return event_dict
        except Exception as e:
            logger.error(f"Error retrieving static events for guild ID {guild_id}: {e}", exc_info=True)
            return {}

    def get_periodic_events(self, guild_id, mode='regular'):
        """Retrieve all periodic events for a guild and mode."""
        try:
            events = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
            event_dict = {
                event.id: {
                    "start_time": event.start_time,
                    "interval": event.interval,
                    "end_time": event.end_time,
                    "message": event.message
                } for event in events
            }
            logger.debug(f"Retrieved {len(event_dict)} periodic events for guild ID {guild_id} in mode '{mode}'.")
            return event_dict
        except Exception as e:
            logger.error(f"Error retrieving periodic events for guild ID {guild_id}: {e}", exc_info=True)
            return {}

    def add_static_event(self, guild_id, time, message, mode='regular'):
        """Add a static event for a guild."""
        logger.info(f"Adding static event for guild ID {guild_id}: Time={time}, Message='{message}', Mode='{mode}'.")
        try:
            new_event = StaticEvent(guild_id=str(guild_id), mode=mode, time=time, message=message)
            self.session.add(new_event)
            self.session.commit()
            logger.info(f"Added static event ID {new_event.id} for guild ID {guild_id}.")
            return new_event.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding static event for guild ID {guild_id}: {e}", exc_info=True)
            raise

    def add_periodic_event(self, guild_id, start_time, interval, end_time, message, mode='regular'):
        """Add a periodic event for a guild."""
        logger.info(f"Adding periodic event for guild ID {guild_id}: Start={start_time}, Interval={interval}, End={end_time}, Message='{message}', Mode='{mode}'.")
        try:
            new_event = PeriodicEvent(
                guild_id=str(guild_id),
                mode=mode,
                start_time=start_time,
                interval=interval,
                end_time=end_time,
                message=message
            )
            self.session.add(new_event)
            self.session.commit()
            logger.info(f"Added periodic event ID {new_event.id} for guild ID {guild_id}.")
            return new_event.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding periodic event for guild ID {guild_id}: {e}", exc_info=True)
            raise

    def remove_event(self, guild_id, event_id):
        """Remove an event (static or periodic) by ID."""
        logger.info(f"Attempting to remove event ID {event_id} for guild ID {guild_id}.")
        try:
            event = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id), id=event_id).first()
            if not event:
                event = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id), id=event_id).first()

            if event:
                self.session.delete(event)
                self.session.commit()
                logger.info(f"Removed event ID {event_id} for guild ID {guild_id}.")
                return True
            else:
                logger.warning(f"Event ID {event_id} not found for guild ID {guild_id}.")
                return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error removing event ID {event_id} for guild ID {guild_id}: {e}", exc_info=True)
            return False

    def close(self):
        """Close the database session."""
        self.session.close()
        logger.debug("EventsManager session closed.")

    def delete_events_for_guild(self, guild_id):
        """Delete all static and periodic events for a specific guild."""
        logger.info(f"Deleting all events for guild ID {guild_id}.")
        try:
            # Delete all static events for the guild
            deleted_static = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id)).delete()
            logger.debug(f"Deleted {deleted_static} static events for guild ID {guild_id}.")

            # Delete all periodic events for the guild
            deleted_periodic = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id)).delete()
            logger.debug(f"Deleted {deleted_periodic} periodic events for guild ID {guild_id}.")

            self.session.commit()
            logger.info(f"All events deleted for guild ID {guild_id}.")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting events for guild ID {guild_id}: {e}", exc_info=True)

    def set_mindful_messages(self, guild_id, enabled):
        """Enable or disable mindful messages for a guild."""
        state = 'enabled' if enabled else 'disabled'
        logger.info(f"Setting mindful messages to {state} for guild ID {guild_id}.")
        try:
            settings = self.session.query(ServerSettings).filter_by(server_id=str(guild_id)).first()
            if settings:
                settings.mindful_messages_enabled = 1 if enabled else 0
                logger.debug(f"Updated ServerSettings for guild ID {guild_id}.")
            else:
                settings = ServerSettings(server_id=str(guild_id), mindful_messages_enabled=1 if enabled else 0)
                self.session.add(settings)
                logger.debug(f"Created new ServerSettings for guild ID {guild_id}.")

            self.session.commit()
            logger.info(f"Mindful messages {'enabled' if enabled else 'disabled'} for guild ID {guild_id}.")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error setting mindful messages for guild ID {guild_id}: {e}", exc_info=True)

    def mindful_messages_enabled(self, guild_id):
        """Check if mindful messages are enabled for a guild."""
        try:
            settings = self.session.query(ServerSettings).filter_by(server_id=str(guild_id)).first()
            enabled = bool(settings.mindful_messages_enabled) if settings else False
            logger.debug(f"Mindful messages enabled for guild ID {guild_id}: {enabled}")
            return enabled
        except Exception as e:
            logger.error(f"Error checking mindful messages status for guild ID {guild_id}: {e}", exc_info=True)
            return False

    def get_random_mindful_message(self):
        """Get a random mindful message."""
        message = random.choice(mindful_messages)["message"]
        logger.debug(f"Selected random mindful message: '{message}'")
        return message
