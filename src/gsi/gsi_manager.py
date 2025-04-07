import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Callable

from src.utils.config import logger
from src.gsi.gsi_state import gsi_state


class GSIManager:
    """
    Manages Dota 2 Game State Integration (GSI) data.

    This class handles processing and storage of GSI data received from the Dota 2 client,
    and provides methods to query the current game state.
    """

    def __init__(self):
        """Initialize the GSI manager."""
        self._callbacks = []
        self._last_update = 0
        logger.info("GSI Manager initialized")

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback function to be called when GSI data is received.

        Args:
            callback: A function that takes the game state as an argument
        """
        self._callbacks.append(callback)
        logger.debug(f"Registered GSI callback: {callback.__name__}")

    def process_request(self, auth_token: str, data: Dict[str, Any]) -> bool:
        """
        Process a GSI request from the Dota 2 client.

        Args:
            auth_token: The authentication token from the request
            data: The GSI data from the request

        Returns:
            bool: True if the request was valid and processed, False otherwise
        """
        # Validate the auth token
        if auth_token != gsi_state.auth_token:
            logger.warning(f"Invalid auth token: {auth_token}")
            return False

        # Process the data
        gsi_state.game_state = data
        self._last_update = time.time()

        # Check game state
        self._update_game_status()

        # Call all registered callbacks
        for callback in self._callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in GSI callback {callback.__name__}: {e}", exc_info=True)

        return True

    def _update_game_status(self) -> None:
        """Update internal game status based on the latest GSI data."""
        try:
            game_state = gsi_state.game_state
            if "map" in game_state:
                map_data = game_state["map"]

                # Check if in a match
                gsi_state.is_in_game = map_data.get("game_state") == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"

                # Log if in game
                if gsi_state.is_in_game:
                    logger.info(f"In game: match ID {map_data.get('matchid')}, mode {map_data.get('game_mode')}")
        except Exception as e:
            logger.error(f"Error updating game status: {e}", exc_info=True)

    def is_in_game(self) -> bool:
        """
        Check if the player is currently in a game.

        Returns:
            bool: True if in game, False otherwise
        """
        # If we haven't received an update in the last 60 seconds, assume not in game
        if time.time() - self._last_update > 60:
            gsi_state.is_in_game = False
        return gsi_state.is_in_game

    def get_game_time(self) -> Optional[float]:
        """
        Get the current game time in seconds.

        Returns:
            Optional[float]: The game time in seconds, or None if not available
        """
        try:
            return gsi_state.game_state.get("map", {}).get("game_time")
        except (KeyError, TypeError):
            return None

    def get_game_mode(self) -> Optional[str]:
        """
        Get the current game mode.

        Returns:
            Optional[str]: The game mode, or None if not available
        """
        try:
            mode_id = gsi_state.game_state.get("map", {}).get("game_mode")
            # Convert mode ID to string (You can expand this with more modes)
            modes = {
                1: "all_pick",
                2: "captains_mode",
                3: "random_draft",
                4: "single_draft",
                5: "all_random",
                22: "turbo"
            }
            return modes.get(mode_id, f"mode_{mode_id}")
        except (KeyError, TypeError):
            return None

    def get_match_id(self) -> Optional[str]:
        """
        Get the current match ID.

        Returns:
            Optional[str]: The match ID, or None if not available
        """
        try:
            return gsi_state.game_state.get("map", {}).get("matchid")
        except (KeyError, TypeError):
            return None

    def get_roshan_state(self) -> Dict[str, Any]:
        """
        Get the current Roshan state.

        Returns:
            Dict: Information about Roshan's state
        """
        result = {
            "alive": True,
            "death_time": None,
            "min_respawn_time": None,
            "max_respawn_time": None
        }

        try:
            if "roshan" in gsi_state.game_state and "alive" in gsi_state.game_state["roshan"]:
                result["alive"] = gsi_state.game_state["roshan"]["alive"]

                if not result["alive"] and "respawn_timer" in gsi_state.game_state["roshan"]:
                    game_time = self.get_game_time() or 0
                    respawn_timer = gsi_state.game_state["roshan"]["respawn_timer"]
                    result["death_time"] = game_time - respawn_timer

                    # Roshan respawn is between 8-11 minutes (480-660 seconds)
                    result["min_respawn_time"] = result["death_time"] + 480
                    result["max_respawn_time"] = result["death_time"] + 660
        except Exception as e:
            logger.error(f"Error getting Roshan state: {e}", exc_info=True)

        return result

    def get_last_update_time(self) -> float:
        """
        Get the time of the last GSI update.

        Returns:
            float: Unix timestamp of the last update
        """
        return self._last_update

    def get_player_team(self) -> Optional[str]:
        """
        Get the team the player is on.

        Returns:
            Optional[str]: 'radiant', 'dire', or None if not available
        """
        try:
            player = gsi_state.game_state.get("player", {})
            team_num = player.get("team_number")

            if team_num == 0:
                return "radiant"
            elif team_num == 1:
                return "dire"
            return None
        except (KeyError, TypeError):
            return None

    def are_glyph_available(self) -> Dict[str, bool]:
        """
        Check if glyphs are available for both teams.

        Returns:
            Dict[str, bool]: Glyph availability for 'radiant' and 'dire'
        """
        result = {
            "radiant": False,
            "dire": False
        }

        try:
            if "buildings" in gsi_state.game_state:
                buildings = gsi_state.game_state["buildings"]
                if "radiant" in buildings and "glyph" in buildings["radiant"]:
                    result["radiant"] = buildings["radiant"]["glyph"]["cooldown"] == 0

                if "dire" in buildings and "glyph" in buildings["dire"]:
                    result["dire"] = buildings["dire"]["glyph"]["cooldown"] == 0
        except Exception as e:
            logger.error(f"Error checking glyph availability: {e}", exc_info=True)

        return result

    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the full game state.

        Returns:
            Dict[str, Any]: The complete GSI game state
        """
        return gsi_state.game_state.copy() if gsi_state.game_state else {}