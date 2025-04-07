"""
Manages GSI sync state between the web API and the Discord bot.
"""
from typing import Dict, Any, Set
from src.utils.config import logger


class GSIStateManager:
    """
    Singleton class to manage GSI state across the Discord bot and web API.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GSIStateManager, cls).__new__(cls)
            cls._instance._synced_guilds = set()
            cls._instance._auth_token = "your_secret_token"  # Default token, should be overridden
            cls._instance._game_state = {}
            cls._instance._is_in_game = False
            logger.info("GSIStateManager initialized")
        return cls._instance

    @property
    def synced_guilds(self) -> Set[int]:
        """Get the set of guild IDs that have GSI sync enabled."""
        return self._synced_guilds

    def toggle_guild_sync(self, guild_id: int) -> bool:
        """
        Toggle GSI sync for a guild.

        Args:
            guild_id: The guild ID to toggle

        Returns:
            bool: True if sync is now enabled, False if disabled
        """
        if guild_id in self._synced_guilds:
            self._synced_guilds.remove(guild_id)
            logger.info(f"Disabled GSI sync for guild {guild_id}")
            return False
        else:
            self._synced_guilds.add(guild_id)
            logger.info(f"Enabled GSI sync for guild {guild_id}")
            return True

    @property
    def auth_token(self) -> str:
        """Get the GSI authentication token."""
        return self._auth_token

    @auth_token.setter
    def auth_token(self, token: str) -> None:
        """Set the GSI authentication token."""
        self._auth_token = token
        logger.info("GSI authentication token updated")

    @property
    def game_state(self) -> Dict[str, Any]:
        """Get the current game state."""
        return self._game_state

    @game_state.setter
    def game_state(self, state: Dict[str, Any]) -> None:
        """Set the current game state."""
        self._game_state = state

    @property
    def is_in_game(self) -> bool:
        """Check if currently in a game."""
        return self._is_in_game

    @is_in_game.setter
    def is_in_game(self, value: bool) -> None:
        """Set the in-game status."""
        self._is_in_game = value


# Create a global instance of the state manager
gsi_state = GSIStateManager()