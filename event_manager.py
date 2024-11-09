# event_manager.py

import logging
from sqlalchemy.orm import sessionmaker
from database import StaticEvent, PeriodicEvent, engine
from event_definitions import regular_periodic_events, regular_static_events

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class EventsManager:
    def __init__(self):
        self.session = SessionLocal()

    def initialize_guild_events(self, guild_id):
        """Copy base template events for a new guild."""
        template_static_events = self.session.query(StaticEvent).filter_by(guild_id=None).all()
        template_periodic_events = self.session.query(PeriodicEvent).filter_by(guild_id=None).all()

        for event in template_static_events:
            guild_event = StaticEvent(guild_id=guild_id, mode=event.mode, time=event.time, message=event.message)
            self.session.add(guild_event)

        for event in template_periodic_events:
            guild_event = PeriodicEvent(guild_id=guild_id, mode=event.mode, start_time=event.start_time,
                                        interval=event.interval, end_time=event.end_time, message=event.message)
            self.session.add(guild_event)

        self.session.commit()
        logger.info(f"Base template events copied for guild_id: {guild_id}")

    def get_static_events(self, guild_id, mode='regular'):
        """Retrieve all static events for a guild and mode."""
        events = self.session.query(StaticEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
        return {event.id: {"time": event.time, "message": event.message} for event in events}

    def get_periodic_events(self, guild_id, mode='regular'):
        """Retrieve all periodic events for a guild and mode."""
        events = self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id), mode=mode).all()
        return {event.id: {"start_time": event.start_time, "interval": event.interval, "end_time": event.end_time,
                           "message": event.message} for event in events}

    def add_static_event(self, guild_id, time, message, mode='regular'):
        """Add a static event for a guild."""
        new_event = StaticEvent(guild_id=str(guild_id), mode=mode, time=time, message=message)
        self.session.add(new_event)
        self.session.commit()
        return new_event.id

    def add_periodic_event(self, guild_id, start_time, interval, end_time, message, mode='regular'):
        """Add a periodic event for a guild."""
        new_event = PeriodicEvent(guild_id=str(guild_id), mode=mode, start_time=start_time, interval=interval,
                                  end_time=end_time, message=message)
        self.session.add(new_event)
        self.session.commit()
        return new_event.id

    def close(self):
        """Close the database session."""
        self.session.close()

    def guild_has_events(self, guild_id):
        """Check if a guild already has any events."""
        return self.session.query(StaticEvent).filter_by(guild_id=str(guild_id)).first() is not None \
            or self.session.query(PeriodicEvent).filter_by(guild_id=str(guild_id)).first() is not None

    def populate_events_for_guild(self, guild_id):
        with SessionLocal() as session:
            # Add static events
            for event_data in regular_static_events:
                static_event = StaticEvent(
                    guild_id=str(guild_id),  # Use guild_id here
                    mode=event_data['mode'],
                    time=event_data['time'],
                    message=event_data['message']
                )
                session.add(static_event)

            # Add periodic events
            for event_data in regular_periodic_events:
                periodic_event = PeriodicEvent(
                    guild_id=str(guild_id),  # Use guild_id here
                    mode=event_data['mode'],
                    start_time=event_data['start_time'],
                    interval=event_data['interval'],
                    end_time=event_data['end_time'],
                    message=event_data['message']
                )
                session.add(periodic_event)
            session.commit()

