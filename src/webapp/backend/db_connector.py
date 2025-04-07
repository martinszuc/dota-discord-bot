"""
Database connector for the Dota Discord Bot Dashboard.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union

# Add the parent directory to the path to import bot modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from src.database import StaticEvent, PeriodicEvent, ServerSettings, SessionLocal

logger = logging.getLogger('DotaDiscordBot.WebApp')

def get_events(guild_id: int, mode: str = 'regular') -> Dict[str, Any]:
    """
    Get all events for a guild.

    Args:
        guild_id (int): The Discord guild ID.
        mode (str, optional): The game mode. Defaults to 'regular'.

    Returns:
        Dict: A dictionary containing static and periodic events.
    """
    try:
        with SessionLocal() as session:
            # Get static events
            static_events = session.query(StaticEvent).filter_by(
                guild_id=str(guild_id), mode=mode).all()

            # Get periodic events
            periodic_events = session.query(PeriodicEvent).filter_by(
                guild_id=str(guild_id), mode=mode).all()

            # Format events for API response
            static_events_dict = {
                event.id: {
                    "id": event.id,
                    "type": "static",
                    "time": event.time,
                    "message": event.message,
                    "mode": event.mode
                } for event in static_events
            }

            periodic_events_dict = {
                event.id: {
                    "id": event.id,
                    "type": "periodic",
                    "start_time": event.start_time,
                    "interval": event.interval,
                    "end_time": event.end_time,
                    "message": event.message,
                    "mode": event.mode
                } for event in periodic_events
            }

            return {
                "static_events": static_events_dict,
                "periodic_events": periodic_events_dict
            }
    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        raise

def add_event(
    guild_id: int,
    event_type: str,
    mode: str = 'regular',
    **kwargs
) -> int:
    """
    Add a new event to the database.

    Args:
        guild_id (int): The Discord guild ID.
        event_type (str): The event type ('static' or 'periodic').
        mode (str, optional): The game mode. Defaults to 'regular'.
        **kwargs: Additional parameters for the event.

    Returns:
        int: The ID of the newly added event.

    Raises:
        ValueError: If the event type is invalid or required parameters are missing.
    """
    try:
        with SessionLocal() as session:
            if event_type == 'static':
                if 'time' not in kwargs or 'message' not in kwargs:
                    raise ValueError("time and message are required for static events")

                event = StaticEvent(
                    guild_id=str(guild_id),
                    mode=mode,
                    time=kwargs['time'],
                    message=kwargs['message']
                )
                session.add(event)
                session.commit()
                return event.id

            elif event_type == 'periodic':
                required_params = ['start_time', 'interval', 'end_time', 'message']
                for param in required_params:
                    if param not in kwargs:
                        raise ValueError(f"{param} is required for periodic events")

                event = PeriodicEvent(
                    guild_id=str(guild_id),
                    mode=mode,
                    start_time=kwargs['start_time'],
                    interval=kwargs['interval'],
                    end_time=kwargs['end_time'],
                    message=kwargs['message']
                )
                session.add(event)
                session.commit()
                return event.id

            else:
                raise ValueError(f"Invalid event type: {event_type}")
    except Exception as e:
        logger.error(f"Error adding event: {e}", exc_info=True)
        raise

def remove_event(guild_id: int, event_id: int) -> bool:
    """
    Remove an event from the database.

    Args:
        guild_id (int): The Discord guild ID.
        event_id (int): The ID of the event to remove.

    Returns:
        bool: True if the event was removed, False otherwise.
    """
    try:
        with SessionLocal() as session:
            # First try to find a static event
            event = session.query(StaticEvent).filter_by(
                guild_id=str(guild_id), id=event_id).first()

            # If not found, try to find a periodic event
            if not event:
                event = session.query(PeriodicEvent).filter_by(
                    guild_id=str(guild_id), id=event_id).first()

            if event:
                session.delete(event)
                session.commit()
                return True

            return False
    except Exception as e:
        logger.error(f"Error removing event: {e}", exc_info=True)
        raise

def get_settings(guild_id: int) -> Dict[str, Any]:
    """
    Get settings for a guild.

    Args:
        guild_id (int): The Discord guild ID.

    Returns:
        Dict: The guild settings.
    """
    try:
        with SessionLocal() as session:
            settings = session.query(ServerSettings).filter_by(
                server_id=str(guild_id)).first()

            if settings:
                return {
                    "prefix": settings.prefix,
                    "timer_channel": settings.timer_channel,
                    "voice_channel": settings.voice_channel,
                    "tts_language": settings.tts_language,
                    "mindful_messages_enabled": bool(settings.mindful_messages_enabled)
                }
            else:
                # Return default settings if none exist
                return {
                    "prefix": "!",
                    "timer_channel": "timer-bot",
                    "voice_channel": "DOTA",
                    "tts_language": "en-US-AriaNeural",
                    "mindful_messages_enabled": False
                }
    except Exception as e:
        logger.error(f"Error getting settings: {e}", exc_info=True)
        raise

def update_settings(guild_id: int, settings_dict: Dict[str, Any]) -> bool:
    """
    Update settings for a guild.

    Args:
        guild_id (int): The Discord guild ID.
        settings_dict (Dict): The settings to update.

    Returns:
        bool: True if the settings were updated, False otherwise.
    """
    try:
        with SessionLocal() as session:
            settings = session.query(ServerSettings).filter_by(
                server_id=str(guild_id)).first()

            if not settings:
                # Create new settings if none exist
                settings = ServerSettings(server_id=str(guild_id))
                session.add(settings)

            # Update settings
            if "prefix" in settings_dict:
                settings.prefix = settings_dict["prefix"]
            if "timer_channel" in settings_dict:
                settings.timer_channel = settings_dict["timer_channel"]
            if "voice_channel" in settings_dict:
                settings.voice_channel = settings_dict["voice_channel"]
            if "tts_language" in settings_dict:
                settings.tts_language = settings_dict["tts_language"]
            if "mindful_messages_enabled" in settings_dict:
                settings.mindful_messages_enabled = 1 if settings_dict["mindful_messages_enabled"] else 0

            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating settings: {e}", exc_info=True)
        raise