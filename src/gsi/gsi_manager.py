import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Callable, Set

from src.utils.config import logger
from src.gsi.gsi_state import gsi_state


class GSIManager:
    """
    Manages Dota 2 Game State Integration (GSI) data.

    This class handles processing and storage of GSI data received from the Dota 2 client,
    and provides methods to query the current game state with enhanced reliability and error handling.
    """

    def __init__(self):
        """Initialize the GSI manager."""
        self._callbacks = []
        self._last_update = 0
        self._last_game_state = {}
        self._data_buffer = []  # Buffer for recent game states
        self._buffer_size = 10  # Store last 10 game states for analysis
        self._disconnect_timeout = 60  # Seconds until considering disconnected
        logger.info("GSI Manager initialized")

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback function to be called when GSI data is received.

        Args:
            callback: A function that takes the game state as an argument
        """
        self._callbacks.append(callback)
        logger.debug(f"Registered GSI callback: {callback.__name__}")

    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Unregister a previously registered callback.

        Args:
            callback: The callback function to unregister

        Returns:
            bool: True if the callback was unregistered, False if it wasn't found
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Unregistered GSI callback: {callback.__name__}")
            return True
        return False

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

        try:
            # Deep copy the data to prevent modification during processing
            game_state = json.loads(json.dumps(data))

            # Add to buffer for analysis
            self._data_buffer.append(game_state)
            if len(self._data_buffer) > self._buffer_size:
                self._data_buffer.pop(0)

            # Store the game state
            gsi_state.game_state = game_state
            self._last_game_state = game_state
            self._last_update = time.time()

            # Check game state
            self._update_game_status()

            # Call all registered callbacks
            for callback in self._callbacks:
                try:
                    callback(game_state)
                except Exception as e:
                    logger.error(f"Error in GSI callback {callback.__name__}: {e}", exc_info=True)

            return True
        except Exception as e:
            logger.error(f"Error processing GSI request: {e}", exc_info=True)
            return False

    def _update_game_status(self) -> None:
        """Update internal game status based on the latest GSI data."""
        try:
            game_state = gsi_state.game_state
            if not game_state:
                logger.debug("No game state available.")
                return

            if "map" in game_state:
                map_data = game_state["map"]

                # Check if in a match
                previous_in_game = gsi_state.is_in_game
                current_in_game = map_data.get("game_state") == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"

                # Detect game state changes
                if current_in_game != previous_in_game:
                    if current_in_game:
                        logger.info(
                            f"Game started: match ID {map_data.get('matchid')}, mode {map_data.get('game_mode')}")
                    else:
                        logger.info(f"Game ended: match ID {map_data.get('matchid')}")

                gsi_state.is_in_game = current_in_game
        except Exception as e:
            logger.error(f"Error updating game status: {e}", exc_info=True)

    def is_in_game(self) -> bool:
        """
        Check if the player is currently in a game.

        Returns:
            bool: True if in game, False otherwise
        """
        # If we haven't received an update in the last timeout period, assume not in game
        if time.time() - self._last_update > self._disconnect_timeout:
            gsi_state.is_in_game = False
            return False
        return gsi_state.is_in_game

    def is_connected(self) -> bool:
        """
        Check if GSI is currently connected.

        Returns:
            bool: True if connected (recent updates), False otherwise
        """
        return time.time() - self._last_update < self._disconnect_timeout

    def get_connection_health(self) -> Dict[str, Any]:
        """
        Get health information about the GSI connection.

        Returns:
            Dict: Information about the GSI connection health
        """
        now = time.time()
        last_update_seconds_ago = now - self._last_update if self._last_update > 0 else None

        return {
            "connected": self.is_connected(),
            "last_update": self._last_update,
            "last_update_seconds_ago": last_update_seconds_ago,
            "in_game": self.is_in_game(),
            "packets_received": len(self._data_buffer)
        }

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
            # Convert mode ID to string
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
        Get the current Roshan state with enhanced reliability.

        Returns:
            Dict: Information about Roshan's state
        """
        result = {
            "alive": True,
            "death_time": None,
            "min_respawn_time": None,
            "max_respawn_time": None,
            "health_percent": 100,
            "last_killed_time": None
        }

        try:
            # First, try to get direct Roshan info if available
            if "roshan" in gsi_state.game_state:
                roshan_data = gsi_state.game_state["roshan"]

                # Check if alive status is provided
                if "alive" in roshan_data:
                    result["alive"] = roshan_data["alive"]

                # Get respawn timer if Roshan is dead
                if not result["alive"] and "respawn_timer" in roshan_data:
                    game_time = self.get_game_time() or 0
                    respawn_timer = roshan_data["respawn_timer"]

                    result["death_time"] = game_time - respawn_timer
                    result["last_killed_time"] = result["death_time"]

                    # Roshan respawn is between 8-11 minutes (480-660 seconds) in regular mode
                    # 4-5.5 minutes (240-330 seconds) in turbo mode
                    if self.get_game_mode() == "turbo":
                        result["min_respawn_time"] = result["death_time"] + 240
                        result["max_respawn_time"] = result["death_time"] + 330
                    else:
                        result["min_respawn_time"] = result["death_time"] + 480
                        result["max_respawn_time"] = result["death_time"] + 660

                # Get health if available
                if "health_percent" in roshan_data:
                    result["health_percent"] = roshan_data["health_percent"]

            # If we don't have direct Roshan status, try to infer from game events
            elif "events" in gsi_state.game_state:
                events = gsi_state.game_state["events"]

                # Look for Roshan kill events
                for event in events:
                    if event.get("type") == "roshan_killed":
                        result["alive"] = False
                        result["death_time"] = event.get("game_time")
                        result["last_killed_time"] = event.get("game_time")

                        # Calculate respawn times
                        if self.get_game_mode() == "turbo":
                            result["min_respawn_time"] = result["death_time"] + 240
                            result["max_respawn_time"] = result["death_time"] + 330
                        else:
                            result["min_respawn_time"] = result["death_time"] + 480
                            result["max_respawn_time"] = result["death_time"] + 660

                        # Set health to 0 since Roshan is dead
                        result["health_percent"] = 0
                        break

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

                # Check Radiant glyph
                if "radiant" in buildings and "glyph" in buildings["radiant"]:
                    result["radiant"] = buildings["radiant"]["glyph"]["cooldown"] == 0

                # Check Dire glyph
                if "dire" in buildings and "glyph" in buildings["dire"]:
                    result["dire"] = buildings["dire"]["glyph"]["cooldown"] == 0

            # If we don't have direct glyph info, try to infer from game events
            elif "events" in gsi_state.game_state:
                events = gsi_state.game_state["events"]

                # Find the most recent glyph events
                radiant_glyph_time = None
                dire_glyph_time = None
                game_time = self.get_game_time() or 0

                for event in events:
                    if event.get("type") == "glyph_used":
                        team = event.get("team")
                        event_time = event.get("game_time", 0)

                        if team == "radiant" and (radiant_glyph_time is None or event_time > radiant_glyph_time):
                            radiant_glyph_time = event_time
                        elif team == "dire" and (dire_glyph_time is None or event_time > dire_glyph_time):
                            dire_glyph_time = event_time

                # Glyph cooldown is 5 minutes (300 seconds) in regular mode
                # 3 minutes (180 seconds) in turbo mode
                cooldown = 180 if self.get_game_mode() == "turbo" else 300

                # Check if glyphs are off cooldown
                if radiant_glyph_time is not None:
                    result["radiant"] = (game_time - radiant_glyph_time) >= cooldown

                if dire_glyph_time is not None:
                    result["dire"] = (game_time - dire_glyph_time) >= cooldown

        except Exception as e:
            logger.error(f"Error checking glyph availability: {e}", exc_info=True)

        return result

    def get_player_hero(self) -> Dict[str, Any]:
        """
        Get information about the player's current hero.

        Returns:
            Dict[str, Any]: Hero information including name, level, health, mana, etc.
        """
        result = {
            "name": None,
            "level": None,
            "health": None,
            "max_health": None,
            "health_percent": None,
            "mana": None,
            "max_mana": None,
            "mana_percent": None
        }

        try:
            hero = gsi_state.game_state.get("hero", {})
            if hero:
                result["name"] = hero.get("name", "").replace("npc_dota_hero_", "")
                result["level"] = hero.get("level")

                # Health information
                result["health"] = hero.get("health")
                result["max_health"] = hero.get("max_health")
                if result["health"] is not None and result["max_health"] is not None and result["max_health"] > 0:
                    result["health_percent"] = round((result["health"] / result["max_health"]) * 100)

                # Mana information
                result["mana"] = hero.get("mana")
                result["max_mana"] = hero.get("max_mana")
                if result["mana"] is not None and result["max_mana"] is not None and result["max_mana"] > 0:
                    result["mana_percent"] = round((result["mana"] / result["max_mana"]) * 100)
        except Exception as e:
            logger.error(f"Error getting player hero information: {e}", exc_info=True)

        return result

    def get_game_state_diff(self) -> Dict[str, Any]:
        """
        Calculate what has changed since the last GSI update.

        Returns:
            Dict[str, Any]: A dictionary of significant changes
        """
        changes = {
            "roshan_killed": False,
            "roshan_respawned": False,
            "glyph_used": None,  # Will be "radiant" or "dire" if used
            "game_started": False,
            "game_ended": False,
            "time_change": 0  # How much game time has passed
        }

        # Need at least 2 game states to compare
        if len(self._data_buffer) < 2:
            return changes

        try:
            # Get current and previous states
            current = self._data_buffer[-1]
            previous = self._data_buffer[-2]

            # Game state changes
            prev_map = previous.get("map", {})
            curr_map = current.get("map", {})

            prev_game_state = prev_map.get("game_state")
            curr_game_state = curr_map.get("game_state")

            # Detect game start/end
            if prev_game_state != "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS" and curr_game_state == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS":
                changes["game_started"] = True
            elif prev_game_state == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS" and curr_game_state != "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS":
                changes["game_ended"] = True

            # Game time changes
            prev_time = prev_map.get("game_time", 0)
            curr_time = curr_map.get("game_time", 0)
            changes["time_change"] = curr_time - prev_time

            # Roshan changes
            prev_roshan = previous.get("roshan", {})
            curr_roshan = current.get("roshan", {})

            if prev_roshan.get("alive", True) and not curr_roshan.get("alive", True):
                changes["roshan_killed"] = True
            elif not prev_roshan.get("alive", True) and curr_roshan.get("alive", True):
                changes["roshan_respawned"] = True

            # Glyph changes
            prev_buildings = previous.get("buildings", {})
            curr_buildings = current.get("buildings", {})

            # Check Radiant glyph
            prev_radiant_glyph = prev_buildings.get("radiant", {}).get("glyph", {}).get("cooldown", 0)
            curr_radiant_glyph = curr_buildings.get("radiant", {}).get("glyph", {}).get("cooldown", 0)
            if prev_radiant_glyph == 0 and curr_radiant_glyph > 0:
                changes["glyph_used"] = "radiant"

            # Check Dire glyph
            prev_dire_glyph = prev_buildings.get("dire", {}).get("glyph", {}).get("cooldown", 0)
            curr_dire_glyph = curr_buildings.get("dire", {}).get("glyph", {}).get("cooldown", 0)
            if prev_dire_glyph == 0 and curr_dire_glyph > 0:
                changes["glyph_used"] = "dire"

        except Exception as e:
            logger.error(f"Error calculating game state diff: {e}", exc_info=True)

        return changes

    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the full game state.

        Returns:
            Dict[str, Any]: The complete GSI game state
        """
        return gsi_state.game_state.copy() if gsi_state.game_state else {}