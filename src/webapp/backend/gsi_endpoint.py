"""
Flask endpoint to receive Dota 2 GSI updates.
"""

from flask import Blueprint, request, jsonify
import time
import json
from typing import Dict, Any

from src.gsi.gsi_manager import GSIManager
from src.gsi.gsi_state import gsi_state
from src.utils.config import logger

# Initialize blueprint
gsi_blueprint = Blueprint('gsi', __name__)

# GSI Manager instance - access to this will be shared with the bot
gsi_manager = GSIManager()

@gsi_blueprint.route('/', methods=['POST'])
def gsi_endpoint():
    """
    Receive GSI updates from Dota 2.

    This endpoint processes Game State Integration updates from the Dota 2 client.
    """
    try:
        if not request.is_json:
            logger.warning("Received non-JSON GSI request")
            return jsonify({
                "status": "error",
                "message": "Request must be JSON"
            }), 400

        # Get the GSI data
        data = request.json

        # Get the auth token from the request
        auth_token = data.get("auth", {}).get("token", "")

        # Process the request
        success = gsi_manager.process_request(auth_token, data)

        if success:
            return jsonify({
                "status": "success",
                "timestamp": time.time()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid authentication"
            }), 401

    except Exception as e:
        logger.error(f"Error processing GSI request: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error processing request: {str(e)}"
        }), 500


@gsi_blueprint.route('/status', methods=['GET'])
def gsi_status():
    """
    Get the current GSI status.

    Returns information about the GSI connection and game state.
    """
    try:
        last_update = gsi_manager.get_last_update_time()
        in_game = gsi_manager.is_in_game()

        # Calculate how long since the last update
        last_update_seconds_ago = time.time() - last_update if last_update > 0 else None

        status = {
            "connected": last_update > 0 and last_update_seconds_ago < 60 if last_update_seconds_ago is not None else False,
            "last_update": last_update,
            "last_update_seconds_ago": last_update_seconds_ago,
            "in_game": in_game,
            "game_mode": gsi_manager.get_game_mode() if in_game else None,
            "match_id": gsi_manager.get_match_id() if in_game else None,
            "game_time": gsi_manager.get_game_time() if in_game else None,
            "player_team": gsi_manager.get_player_team() if in_game else None
        }

        return jsonify({
            "status": "success",
            "data": status
        })

    except Exception as e:
        logger.error(f"Error getting GSI status: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error getting status: {str(e)}"
        }), 500


@gsi_blueprint.route('/sync', methods=['POST'])
def toggle_gsi_sync():
    """
    Toggle GSI auto-sync for a guild.

    This endpoint allows the web interface to toggle whether a guild
    should have GSI auto-sync enabled.
    """
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Request must be JSON"
            }), 400

        # Get the guild ID from the request
        guild_id = request.json.get('guild_id')

        if not guild_id:
            return jsonify({
                "status": "error",
                "message": "guild_id is required"
            }), 400

        # Toggle sync for this guild
        is_enabled = gsi_state.toggle_guild_sync(int(guild_id))

        return jsonify({
            "status": "success",
            "data": {
                "guild_id": guild_id,
                "sync_enabled": is_enabled
            }
        })

    except Exception as e:
        logger.error(f"Error toggling GSI sync: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error toggling GSI sync: {str(e)}"
        }), 500