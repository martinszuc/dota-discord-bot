"""
Connector for interacting with the Discord bot.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path to import bot modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from src.bot import game_timers
from src.managers.event_manager import EventsManager
from src.utils.config import logger

class BotConnector:
    """
    Connector class to interact with the Discord bot.
    Provides methods to control the bot and retrieve information.
    """

    def __init__(self):
        """Initialize the bot connector."""
        self.events_manager = EventsManager()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.logger = logging.getLogger('DotaDiscordBot.WebApp')

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the bot.

        Returns:
            Dict: The status information including active timers and bot state.
        """
        try:
            active_timers = {guild_id: {
                "guild_id": guild_id,
                "mode": timer.mode,
                "elapsed_time": timer.time_elapsed,
                "paused": timer.paused,
                "roshan_active": timer.roshan_timer.is_running,
                "glyph_active": timer.glyph_timer.is_running,
                "tormentor_active": timer.tormentor_timer.is_running
            } for guild_id, timer in game_timers.items()}

            return {
                "active_timers_count": len(active_timers),
                "active_timers": active_timers,
                "bot_running": True  # Assuming the bot is running if this code is executed
            }
        except Exception as e:
            self.logger.error(f"Error getting bot status: {e}", exc_info=True)
            raise

    def get_active_timers(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all active game timers.

        Returns:
            Dict: A dictionary of active timers keyed by guild_id.
        """
        try:
            return {guild_id: {
                "guild_id": guild_id,
                "mode": timer.mode,
                "elapsed_time": timer.time_elapsed,
                "paused": timer.paused,
                "roshan_active": timer.roshan_timer.is_running,
                "glyph_active": timer.glyph_timer.is_running,
                "tormentor_active": timer.tormentor_timer.is_running,
                "recent_events": timer.recent_events
            } for guild_id, timer in game_timers.items()}
        except Exception as e:
            self.logger.error(f"Error getting active timers: {e}", exc_info=True)
            raise

    def _run_async(self, coro):
        """
        Run an asynchronous coroutine in a synchronous context.

        Args:
            coro: The coroutine to execute.

        Returns:
            The result of the coroutine.
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def start_timer(self, guild_id: int, countdown: str, mode: str = 'regular') -> Dict[str, Any]:
        """
        Start a new game timer.

        Args:
            guild_id (int): The Discord guild ID.
            countdown (str): The countdown string (e.g., "10:00" or "-5:00").
            mode (str, optional): The game mode. Defaults to 'regular'.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import start_game

            # Since start_game is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the start_game command
            self._run_async(start_game(ctx, countdown, mode))

            return {"message": f"Game timer started with countdown '{countdown}' in mode '{mode}'"}
        except Exception as e:
            self.logger.error(f"Error starting timer: {e}", exc_info=True)
            raise

    def stop_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Stop an active game timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import stop_game

            # Since stop_game is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the stop_game command
            self._run_async(stop_game(ctx))

            return {"message": "Game timer stopped"}
        except Exception as e:
            self.logger.error(f"Error stopping timer: {e}", exc_info=True)
            raise

    def pause_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Pause an active game timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import pause_game

            # Since pause_game is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the pause_game command
            self._run_async(pause_game(ctx))

            return {"message": "Game timer paused"}
        except Exception as e:
            self.logger.error(f"Error pausing timer: {e}", exc_info=True)
            raise

    def unpause_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Unpause an active game timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import unpause_game

            # Since unpause_game is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the unpause_game command
            self._run_async(unpause_game(ctx))

            return {"message": "Game timer unpaused"}
        except Exception as e:
            self.logger.error(f"Error unpausing timer: {e}", exc_info=True)
            raise

    def start_roshan_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Start the Roshan timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import rosh_timer_command

            # Since rosh_timer_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the rosh_timer_command
            self._run_async(rosh_timer_command(ctx))

            return {"message": "Roshan timer started"}
        except Exception as e:
            self.logger.error(f"Error starting Roshan timer: {e}", exc_info=True)
            raise

    def cancel_roshan_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Cancel the Roshan timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import cancel_rosh_command

            # Since cancel_rosh_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the cancel_rosh_command
            self._run_async(cancel_rosh_command(ctx))

            return {"message": "Roshan timer cancelled"}
        except Exception as e:
            self.logger.error(f"Error cancelling Roshan timer: {e}", exc_info=True)
            raise

    def start_glyph_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Start the Glyph timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import glyph_timer_command

            # Since glyph_timer_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the glyph_timer_command
            self._run_async(glyph_timer_command(ctx))

            return {"message": "Glyph timer started"}
        except Exception as e:
            self.logger.error(f"Error starting Glyph timer: {e}", exc_info=True)
            raise

    def cancel_glyph_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Cancel the Glyph timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import cancel_glyph_command

            # Since cancel_glyph_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the cancel_glyph_command
            self._run_async(cancel_glyph_command(ctx))

            return {"message": "Glyph timer cancelled"}
        except Exception as e:
            self.logger.error(f"Error cancelling Glyph timer: {e}", exc_info=True)
            raise

    def start_tormentor_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Start the Tormentor timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import tormentor_timer_command

            # Since tormentor_timer_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the tormentor_timer_command
            self._run_async(tormentor_timer_command(ctx))

            return {"message": "Tormentor timer started"}
        except Exception as e:
            self.logger.error(f"Error starting Tormentor timer: {e}", exc_info=True)
            raise

    def cancel_tormentor_timer(self, guild_id: int) -> Dict[str, Any]:
        """
        Cancel the Tormentor timer.

        Args:
            guild_id (int): The Discord guild ID.

        Returns:
            Dict: The result of the operation.
        """
        try:
            from src.bot import cancel_tormentor_command

            # Since cancel_tormentor_command is a command, we need to mock a context
            class MockContext:
                def __init__(self, guild_id):
                    self.guild = type('obj', (object,), {
                        'id': guild_id,
                        'text_channels': [],
                        'voice_channels': []
                    })
                    self.author = type('obj', (object,), {
                        'name': 'WebApp'
                    })
                    self.send = self._mock_send

                async def _mock_send(self, message):
                    logger.info(f"[WebApp] {message}")
                    return None

            ctx = MockContext(guild_id)

            # Run the cancel_tormentor_command
            self._run_async(cancel_tormentor_command(ctx))

            return {"message": "Tormentor timer cancelled"}
        except Exception as e:
            self.logger.error(f"Error cancelling Tormentor timer: {e}", exc_info=True)
            raise

    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get bot logs.

        Args:
            limit (int, optional): The maximum number of logs to retrieve. Defaults to 100.
            offset (int, optional): The offset for pagination. Defaults to 0.

        Returns:
            List[Dict]: The list of log entries.
        """
        try:
            from src.utils.config import LOG_FILE_PATH

            logs = []
            if os.path.exists(LOG_FILE_PATH):
                with open(LOG_FILE_PATH, 'r') as f:
                    lines = f.readlines()

                # Apply offset and limit
                logs = [self._parse_log_line(line) for line in lines[-limit-offset:len(lines)-offset]]

            return logs
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}", exc_info=True)
            raise

    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a log line into a structured format.

        Args:
            line (str): The log line to parse.

        Returns:
            Dict: The parsed log entry.
        """
        try:
            parts = line.split(' - ', 4)
            if len(parts) >= 5:
                timestamp, level, logger_name, func_name_with_line, message = parts
                func_parts = func_name_with_line.split(' - ')
                if len(func_parts) == 2:
                    func_name, line_num = func_parts
                else:
                    func_name, line_num = func_name_with_line, ""

                return {
                    "timestamp": timestamp.strip(),
                    "level": level.strip(),
                    "logger": logger_name.strip(),
                    "function": func_name.strip(),
                    "line": line_num.strip(),
                    "message": message.strip()
                }
            else:
                return {
                    "timestamp": "",
                    "level": "",
                    "logger": "",
                    "function": "",
                    "line": "",
                    "message": line.strip()
                }
        except Exception:
            return {
                "timestamp": "",
                "level": "",
                "logger": "",
                "function": "",
                "line": "",
                "message": line.strip()
            }