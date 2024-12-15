from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

from src.utils.config import DATABASE_URL

# Initialize the SQLAlchemy engine with the provided database URL.
# The 'check_same_thread' parameter is set to False to allow usage with multiple threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class for database interactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions.
Base = declarative_base()


class ServerSettings(Base):
    """
    Represents server-specific settings in the database.

    Attributes:
        id (int): Primary key for the server settings record.
        server_id (str): Unique identifier for the Discord server.
        prefix (str): Command prefix used by the bot in the server.
        timer_channel (str): Name of the text channel designated for timer announcements.
        voice_channel (str): Name of the voice channel designated for TTS announcements.
        tts_language (str): Language setting for text-to-speech announcements.
        mindful_messages_enabled (int): Flag indicating if mindful messages are enabled (1) or disabled (0).
    """
    __tablename__ = "server_settings"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, unique=True, index=True, nullable=False)
    prefix = Column(String, default="!", nullable=False)
    timer_channel = Column(String, default="timer-bot", nullable=False)
    voice_channel = Column(String, default="DOTA", nullable=False)
    tts_language = Column(String, default="en-US-AriaNeural", nullable=False)
    mindful_messages_enabled = Column(Integer, default=0, nullable=False)


class StaticEvent(Base):
    """
    Represents static events in the database.

    Attributes:
        id (int): Primary key for the static event record.
        guild_id (str): Identifier for the Discord guild/server.
        mode (str): Game mode ('regular' or 'turbo') associated with the event.
        time (int): Time in seconds when the event should trigger.
        message (str): Message to announce when the event triggers.
    """
    __tablename__ = "static_events"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=False)
    mode = Column(String, index=True, nullable=False)  # 'regular' or 'turbo'
    time = Column(Integer, nullable=False)  # Stored as seconds
    message = Column(String, nullable=False)


class PeriodicEvent(Base):
    """
    Represents periodic events in the database.

    Attributes:
        id (int): Primary key for the periodic event record.
        guild_id (str): Identifier for the Discord guild/server.
        mode (str): Game mode ('regular' or 'turbo') associated with the event.
        start_time (int): Time in seconds when the event series starts.
        interval (int): Interval in seconds between consecutive event triggers.
        end_time (int): Time in seconds when the event series ends.
        message (str): Message to announce when the event triggers.
    """
    __tablename__ = "periodic_events"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=False)
    mode = Column(String, index=True, nullable=False)  # 'regular' or 'turbo'
    start_time = Column(Integer, nullable=False)  # in seconds
    interval = Column(Integer, nullable=False)  # in seconds
    end_time = Column(Integer, nullable=False)  # in seconds
    message = Column(String, nullable=False)


# Create all tables in the database based on the defined models.
Base.metadata.create_all(bind=engine)
