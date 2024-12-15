# scripts/populate_events.py

from sqlalchemy.orm import sessionmaker

from src.database import StaticEvent, PeriodicEvent, engine
from src.event_definitions import regular_static_events, regular_periodic_events, turbo_static_events, \
    turbo_periodic_events
from src.utils.config import logger  # Use the logger from config

# Session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def populate_base_template_events():
    """Populate database with base template events."""
    with SessionLocal() as session:
        session.query(StaticEvent).delete()
        session.query(PeriodicEvent).delete()
        logger.info("Deleted existing StaticEvent and PeriodicEvent records.")

        # Add static and periodic events for 'regular' and 'turbo' modes
        for event_data in regular_static_events:
            event = StaticEvent(mode=event_data['mode'], time=event_data['time'], message=event_data['message'])
            session.add(event)
            logger.debug(f"Added static event: {event}")

        for event_data in regular_periodic_events:
            event = PeriodicEvent(mode=event_data['mode'], start_time=event_data['start_time'],
                                  interval=event_data['interval'], end_time=event_data['end_time'],
                                  message=event_data['message'])
            session.add(event)
            logger.debug(f"Added periodic event: {event}")

        for event_data in turbo_static_events:
            event = StaticEvent(mode=event_data['mode'], time=event_data['time'], message=event_data['message'])
            session.add(event)
            logger.debug(f"Added turbo static event: {event}")

        for event_data in turbo_periodic_events:
            event = PeriodicEvent(mode=event_data['mode'], start_time=event_data['start_time'],
                                  interval=event_data['interval'], end_time=event_data['end_time'],
                                  message=event_data['message'])
            session.add(event)
            logger.debug(f"Added turbo periodic event: {event}")

        session.commit()
        logger.info("Base template events populated successfully.")

if __name__ == "__main__":
    populate_base_template_events()
