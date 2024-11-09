# scripts/populate_events.py

import sys
import os

# Add the project root directory to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import StaticEvent, PeriodicEvent, Base
from event_definitions import (
    regular_static_events,
    regular_periodic_events,
    turbo_static_events,
    turbo_periodic_events,
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - using SQLite for simplicity
DATABASE_URL = "sqlite:///bot.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions
Base.metadata.create_all(bind=engine)

def clear_database(session):
    """Clear the StaticEvent and PeriodicEvent tables."""
    try:
        session.query(StaticEvent).delete()
        session.query(PeriodicEvent).delete()
        session.commit()
        logger.info("Cleared StaticEvent and PeriodicEvent tables.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing database: {e}")
        raise

def populate_events():
    """Populate the database with predefined events."""
    try:
        with SessionLocal() as session:
            clear_database(session)
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
            logger.info("Database populated with default events.")
    except Exception as e:
        logger.error(f"Failed to populate events: {e}")

if __name__ == "__main__":
    populate_events()
