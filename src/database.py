# database.py

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml
import os

# Load configuration
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/config.yaml")

with open(config_path, "r") as file:
    config = yaml.safe_load(file)
DATABASE_URL = config.get("database_url", "sqlite:///bot.db")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions
Base = declarative_base()

class ServerSettings(Base):
    """Model for storing server-specific settings."""
    __tablename__ = "server_settings"
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, unique=True, index=True, nullable=False)
    prefix = Column(String, default="!", nullable=False)
    timer_channel = Column(String, default="timer-bot", nullable=False)
    voice_channel = Column(String, default="DOTA", nullable=False)
    tts_language = Column(String, default="en-US-AriaNeural", nullable=False)

class StaticEvent(Base):
    """Model for storing static events."""
    __tablename__ = "static_events"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=False)
    mode = Column(String, index=True, nullable=False)  # 'regular' or 'turbo'
    time = Column(Integer, nullable=False)  # Stored as seconds
    message = Column(String, nullable=False)

class PeriodicEvent(Base):
    """Model for storing periodic events."""
    __tablename__ = "periodic_events"
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=False)
    mode = Column(String, index=True, nullable=False)  # 'regular' or 'turbo'
    start_time = Column(Integer, nullable=False)  # in seconds
    interval = Column(Integer, nullable=False)    # in seconds
    end_time = Column(Integer, nullable=False)    # in seconds
    message = Column(String, nullable=False)

# Create all tables in the database
Base.metadata.create_all(bind=engine)
