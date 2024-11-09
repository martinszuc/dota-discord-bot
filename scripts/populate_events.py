from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import StaticEvent, PeriodicEvent, Base
from event_definitions import (
    regular_static_events,
    regular_periodic_events,
    turbo_static_events,
    turbo_periodic_events,
)

# Database URL - using SQLite for simplicity
DATABASE_URL = "sqlite:///bot.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions
Base.metadata.create_all(bind=engine)

def populate_events():
    session = SessionLocal()

    # Add regular static events
    for event_id, event_data in regular_static_events.items():
        static_event = StaticEvent(
            id=event_id,
            mode='regular',
            time=event_data['time'],
            message=event_data['message']
        )
        session.merge(static_event)

    # Add regular periodic events
    for event_id, event_data in regular_periodic_events.items():
        periodic_event = PeriodicEvent(
            id=event_id,
            mode='regular',
            start_time=event_data['start_time'],
            interval=event_data['interval'],
            end_time=event_data['end_time'],
            message=event_data['message']
        )
        session.merge(periodic_event)

    # Add turbo static events
    for event_id, event_data in turbo_static_events.items():
        static_event = StaticEvent(
            id=event_id,
            mode='turbo',
            time=event_data['time'],
            message=event_data['message']
        )
        session.merge(static_event)

    # Add turbo periodic events
    for event_id, event_data in turbo_periodic_events.items():
        periodic_event = PeriodicEvent(
            id=event_id,
            mode='turbo',
            start_time=event_data['start_time'],
            interval=event_data['interval'],
            end_time=event_data['end_time'],
            message=event_data['message']
        )
        session.merge(periodic_event)

    session.commit()
    session.close()
    print("Database populated with default events")

if __name__ == "__main__":
    populate_events()
