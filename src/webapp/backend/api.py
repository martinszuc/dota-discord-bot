"""
API endpoints for the Dota Discord Bot Dashboard.
"""
import asyncio

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional, Union

from .bot_connector import BotConnector
from .db_connector import get_events, add_event, remove_event, get_settings, update_settings

# Initialize blueprint
api_blueprint = Blueprint('api', __name__)
bot_connector = BotConnector()


# Status endpoint
@api_blueprint.route('/status', methods=['GET'])
def get_status() -> Dict[str, Any]:
    """Get the current status of the bot."""
    try:
        status = bot_connector.get_status()
        return jsonify({
            "status": "success",
            "data": status
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Game timers endpoints
@api_blueprint.route('/timers', methods=['GET'])
def get_timers() -> Dict[str, Any]:
    """Get all active game timers."""
    try:
        timers = bot_connector.get_active_timers()
        return jsonify({
            "status": "success",
            "data": timers
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/timers/start', methods=['POST'])
def start_timer() -> Dict[str, Any]:
    """Start a new game timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')
        countdown = data.get('countdown')
        mode = data.get('mode', 'regular')

        if not guild_id or not countdown:
            return jsonify({
                "status": "error",
                "message": "guild_id and countdown are required"
            }), 400

        result = bot_connector.start_timer(guild_id, countdown, mode)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/timers/stop', methods=['POST'])
def stop_timer() -> Dict[str, Any]:
    """Stop an active game timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        result = bot_connector.stop_timer(guild_id)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/timers/pause', methods=['POST'])
def pause_timer() -> Dict[str, Any]:
    """Pause an active game timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        result = bot_connector.pause_timer(guild_id)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/timers/unpause', methods=['POST'])
def unpause_timer() -> Dict[str, Any]:
    """Unpause an active game timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        result = bot_connector.unpause_timer(guild_id)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Events endpoints
@api_blueprint.route('/events', methods=['GET'])
def get_all_events() -> Dict[str, Any]:
    """Get all events for a guild."""
    guild_id = request.args.get('guild_id')
    mode = request.args.get('mode', 'regular')

    if not guild_id:
        return jsonify({
            "status": "error",
            "message": "guild_id is required"
        }), 400

    try:
        events = get_events(guild_id, mode)
        return jsonify({
            "status": "success",
            "data": events
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/events', methods=['POST'])
def add_new_event() -> Dict[str, Any]:
    """Add a new event."""
    data = request.json
    try:
        event_type = data.get('type')
        guild_id = data.get('guild_id')
        mode = data.get('mode', 'regular')

        if not event_type or not guild_id:
            return jsonify({
                "status": "error",
                "message": "type and guild_id are required"
            }), 400

        if event_type == 'static':
            time = data.get('time')
            message = data.get('message')

            if not time or not message:
                return jsonify({
                    "status": "error",
                    "message": "time and message are required for static events"
                }), 400

            event_id = add_event(guild_id, event_type, mode, time=time, message=message)
        elif event_type == 'periodic':
            start_time = data.get('start_time')
            interval = data.get('interval')
            end_time = data.get('end_time')
            message = data.get('message')

            if not start_time or not interval or not end_time or not message:
                return jsonify({
                    "status": "error",
                    "message": "start_time, interval, end_time, and message are required for periodic events"
                }), 400

            event_id = add_event(guild_id, event_type, mode,
                                 start_time=start_time, interval=interval,
                                 end_time=end_time, message=message)
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid event type"
            }), 400

        return jsonify({
            "status": "success",
            "data": {"event_id": event_id}
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id: int) -> Dict[str, Any]:
    """Delete an event."""
    guild_id = request.args.get('guild_id')

    if not guild_id:
        return jsonify({
            "status": "error",
            "message": "guild_id is required"
        }), 400

    try:
        success = remove_event(guild_id, event_id)
        if success:
            return jsonify({
                "status": "success",
                "data": {"message": f"Event {event_id} deleted successfully"}
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Event {event_id} not found"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Settings endpoints
@api_blueprint.route('/settings', methods=['GET'])
def get_all_settings() -> Dict[str, Any]:
    """Get all settings for a guild."""
    guild_id = request.args.get('guild_id')

    if not guild_id:
        return jsonify({
            "status": "error",
            "message": "guild_id is required"
        }), 400

    try:
        settings = get_settings(guild_id)
        return jsonify({
            "status": "success",
            "data": settings
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/settings', methods=['PUT'])
def update_all_settings() -> Dict[str, Any]:
    """Update settings for a guild."""
    data = request.json
    try:
        guild_id = data.get('guild_id')
        settings = data.get('settings')

        if not guild_id or not settings:
            return jsonify({
                "status": "error",
                "message": "guild_id and settings are required"
            }), 400

        success = update_settings(guild_id, settings)
        if success:
            return jsonify({
                "status": "success",
                "data": {"message": "Settings updated successfully"}
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to update settings"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Special commands endpoints
@api_blueprint.route('/commands/roshan', methods=['POST'])
def roshan_command() -> Dict[str, Any]:
    """Trigger Roshan timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')
        action = data.get('action', 'start')  # start or cancel

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        if action == 'start':
            result = bot_connector.start_roshan_timer(guild_id)
        elif action == 'cancel':
            result = bot_connector.cancel_roshan_timer(guild_id)
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid action"
            }), 400

        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/commands/glyph', methods=['POST'])
def glyph_command() -> Dict[str, Any]:
    """Trigger Glyph timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')
        action = data.get('action', 'start')  # start or cancel

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        if action == 'start':
            result = bot_connector.start_glyph_timer(guild_id)
        elif action == 'cancel':
            result = bot_connector.cancel_glyph_timer(guild_id)
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid action"
            }), 400

        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@api_blueprint.route('/commands/tormentor', methods=['POST'])
def tormentor_command() -> Dict[str, Any]:
    """Trigger Tormentor timer."""
    data = request.json
    try:
        guild_id = data.get('guild_id')
        action = data.get('action', 'start')  # start or cancel

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        if action == 'start':
            result = bot_connector.start_tormentor_timer(guild_id)
        elif action == 'cancel':
            result = bot_connector.cancel_tormentor_timer(guild_id)
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid action"
            }), 400

        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# Logs endpoint
@api_blueprint.route('/logs', methods=['GET'])
def get_logs() -> Dict[str, Any]:
    """Get bot logs."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    try:
        logs = bot_connector.get_logs(limit, offset)
        return jsonify({
            "status": "success",
            "data": logs
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# GSI-related commands
@api_blueprint.route('/commands/gsi-sync', methods=['POST'])
def toggle_gsi_sync():
    """Toggle GSI auto-sync for a guild."""
    data = request.json
    try:
        guild_id = data.get('guild_id')

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        # Mock the context for the command
        class MockContext:
            def __init__(self, guild_id):
                self.guild = type('obj', (object,), {
                    'id': guild_id,
                })
                self.channel = type('obj', (object,), {
                    'id': None,
                    'send': lambda *args, **kwargs: None
                })
                self.author = type('obj', (object,), {
                    'name': 'WebApp'
                })

        ctx = MockContext(guild_id)

        # Find the GSI cog and execute the command
        from discord.ext.commands import Bot
        gsi_cog = bot.get_cog('GSICog')
        if gsi_cog:
            asyncio.create_task(gsi_cog.gsi_sync(ctx))
            return jsonify({
                "status": "success",
                "data": {"message": "GSI sync toggled"}
            })
        else:
            return jsonify({
                "status": "error",
                "message": "GSI cog not found"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500