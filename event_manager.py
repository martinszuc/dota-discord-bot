# event_manager.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import yaml
import logging

from database import Base, engine  # Importing from database.py to reuse the engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True)  # 'static' or 'periodic'
    time = Column(Integer, nullable=True)  # For static events (stored as seconds)
    start_time = Column(Integer, nullable=True)  # For periodic events (stored as seconds)
    interval = Column(Integer, nullable=True)    # For periodic events (stored as seconds)
    end_time = Column(Integer, nullable=True)    # For periodic events (stored as seconds)
    message = Column(String, nullable=False)
    mode = Column(String, default='regular')     # 'regular' or 'turbo'

# Ensure that the events table exists
Base.metadata.create_all(bind=engine)

class EventsManager:
    """Class to manage events for different game modes."""

    def __init__(self):
        self.session = SessionLocal()

    def get_events(self, guild_id, mode='regular'):
        """Retrieve all events for the specified guild and mode."""
        try:
            events = self.session.query(Event).filter_by(guild_id=str(guild_id), mode=mode).all()
            static_events = {}
            periodic_events = {}
            for event in events:
                if event.event_type == 'static' and event.time is not None:
                    static_events[event.id] = {
                        "time": event.time,
                        "message": event.message
                    }
                elif event.event_type == 'periodic' and event.start_time is not None:
                    periodic_events[event.id] = {
                        "start_time": event.start_time,
                        "interval": event.interval,
                        "end_time": event.end_time,
                        "message": event.message
                    }
            return static_events, periodic_events
        except Exception as e:
            logger.error(f"Error retrieving events: {e}", exc_info=True)
            return {}, {}

    def add_static_event(self, guild_id, time, message, mode='regular'):
        """Add a static event."""
        try:
            new_event = Event(
                guild_id=str(guild_id),
                event_type='static',
                time=time,
                message=message,
                mode=mode
            )
            self.session.add(new_event)
            self.session.commit()
            logger.info(f"Added static event ID {new_event.id} for guild {guild_id}.")
            return new_event.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding static event: {e}", exc_info=True)
            raise

    def add_periodic_event(self, guild_id, start_time, interval, end_time, message, mode='regular'):
        """Add a periodic event."""
        try:
            new_event = Event(
                guild_id=str(guild_id),
                event_type='periodic',
                start_time=start_time,
                interval=interval,
                end_time=end_time,
                message=message,
                mode=mode
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
        """Remove an event by ID."""
        try:
            event = self.session.query(Event).filter_by(guild_id=str(guild_id), id=event_id).first()
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
            logger.error(f"Error removing event: {e}", exc_info=True)
            return False

    def list_events(self, guild_id, mode='regular'):
        """List all events for a guild and mode."""
        try:
            events = self.session.query(Event).filter_by(guild_id=str(guild_id), mode=mode).all()
            return events
        except Exception as e:
            logger.error(f"Error listing events: {e}", exc_info=True)
            return []

    def close(self):
        """Close the database session."""
        self.session.close()
