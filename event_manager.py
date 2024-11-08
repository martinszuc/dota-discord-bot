# event_manager.py

import logging
from sqlalchemy.orm import sessionmaker
from database import StaticEvent, PeriodicEvent, engine
from event_definitions import regular_static_events, regular_periodic_events, turbo_static_events, turbo_periodic_events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class EventsManager:
    """Class to manage static and periodic events for different game modes."""

    def __init__(self):
        self.session = SessionLocal()

    def guild_has_events(self, guild_id):
        """Check if a guild already has any events."""
        has_static = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id)).first() is not None
        has_periodic = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id)).first() is not None
        return has_static or has_periodic

    def populate_events_for_guild(self, guild_id):
        """Populate the database with base events for a specific guild."""
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

            self.session.commit()
            logger.info(f"Populated events for guild ID: {guild_id}")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error populating events for guild ID {guild_id}: {e}", exc_info=True)

    def get_static_events(self, guild_id, mode='regular'):
        """Retrieve all static events for a guild and mode."""
        try:
            events = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
            return {event.id: {"time": event.time, "message": event.message} for event in events}
        except Exception as e:
            logger.error(f"Error retrieving static events: {e}", exc_info=True)
            return {}

    def get_periodic_events(self, guild_id, mode='regular'):
        """Retrieve all periodic events for a guild and mode."""
        try:
            events = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
            return {
                event.id: {
                    "start_time": event.start_time,
                    "interval": event.interval,
                    "end_time": event.end_time,
                    "message": event.message
                } for event in events
            }
        except Exception as e:
            logger.error(f"Error retrieving periodic events: {e}", exc_info=True)
            return {}

    def add_static_event(self, guild_id, time, message, mode='regular'):
        """Add a static event for a guild."""
        try:
            new_event = StaticEvent(guild_id=str(guild_id), mode=mode, time=time, message=message)
            self.session.add(new_event)
            self.session.commit()
            logger.info(f"Added static event ID {new_event.id} for guild {guild_id}.")
            return new_event.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding static event: {e}", exc_info=True)
            raise

    def add_periodic_event(self, guild_id, start_time, interval, end_time, message, mode='regular'):
        """Add a periodic event for a guild."""
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
            logger.info(f"Added periodic event ID {new_event.id} for guild {guild_id}.")
            return new_event.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding periodic event: {e}", exc_info=True)
            raise

    def remove_event(self, guild_id, event_id):
        """Remove an event (static or periodic) by ID."""
        try:
            event = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id), id=event_id).first()
            if not event:
                event = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id), id=event_id).first()

            if event:
                self.session.delete(event)
                self.session.commit()
                logger.info(f"Removed event ID {event_id} for guild {guild_id}.")
                return True
            else:
                logger.warning(f"Event ID {event_id} not found for guild {guild_id}.")
                return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error removing event ID {event_id} for guild {guild_id}: {e}", exc_info=True)
            return False

    def close(self):
        """Close the database session."""
        self.session.close()
