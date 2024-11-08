# events.py

from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

DATABASE_URL = config.get("database_url", "sqlite:///bot.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, index=True)
    event_type = Column(String, index=True)  # 'static' or 'periodic'
    time = Column(String, nullable=True)
    start_time = Column(String, nullable=True)
    interval = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    message = Column(String)
    mode = Column(String, default='regular')  # 'regular' or 'turbo'


# Create tables
Base.metadata.create_all(bind=engine)


class EventsManager:
    """Class to manage events for different game modes."""

    def __init__(self):
        self.session = SessionLocal()

    def get_events(self, guild_id, mode='regular'):
        """Retrieve all events for the specified guild and mode."""
        events = self.session.query(Event).filter_by(guild_id=guild_id, mode=mode).all()
        static_events = {}
        periodic_events = {}
        for event in events:
            if event.event_type == 'static':
                static_events[event.id] = {
                    "time": event.time,
                    "message": event.message
                }
            elif event.event_type == 'periodic':
                periodic_events[event.id] = {
                    "start_time": event.start_time,
                    "interval": event.interval,
                    "end_time": event.end_time,
                    "message": event.message
                }
        return static_events, periodic_events

    def add_static_event(self, guild_id, time, message, mode='regular'):
        """Add a static event."""
        new_event = Event(
            guild_id=guild_id,
            event_type='static',
            time=time,
            message=message,
            mode=mode
        )
        self.session.add(new_event)
        self.session.commit()
        return new_event.id

    def add_periodic_event(self, guild_id, start_time, interval, end_time, message, mode='regular'):
        """Add a periodic event."""
        new_event = Event(
            guild_id=guild_id,
            event_type='periodic',
            start_time=start_time,
            interval=interval,
            end_time=end_time,
            message=message,
            mode=mode
        )
        self.session.add(new_event)
        self.session.commit()
        return new_event.id

    def remove_event(self, guild_id, event_id):
        """Remove an event by ID."""
        event = self.session.query(Event).filter_by(guild_id=guild_id, id=event_id).first()
        if event:
            self.session.delete(event)
            self.session.commit()
            return True
        else:
            return False

    def list_events(self, guild_id, mode='regular'):
        """List all events for a guild and mode."""
        events = self.session.query(Event).filter_by(guild_id=guild_id, mode=mode).all()
        return events

    def close(self):
        self.session.close()
