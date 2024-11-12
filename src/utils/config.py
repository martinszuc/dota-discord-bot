# src/utils/config.py

import os
import yaml
import logging
from logging.handlers import RotatingFileHandler

# Set base directory to the current directory where the script is running
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TTS_CACHE_DIR = os.path.join(BASE_DIR, "tts_cache")

# Load configuration data
def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")

# Load the config once
CONFIG = load_config()

# Constants for application settings
PREFIX = CONFIG.get("prefix", "!")
TIMER_CHANNEL_NAME = CONFIG.get("timer_channel", "timer-bot")
VOICE_CHANNEL_NAME = CONFIG.get("voice_channel", "DOTA")
DATABASE_URL = CONFIG.get("database_url", "sqlite:///bot.db")
CONSOLE_LOG_LEVEL = CONFIG.get("console_log_level", "INFO").upper()  # Default to INFO if not set

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

# Set up logging with advanced configuration
LOG_FILE_PATH = os.path.join(LOG_DIR, "bot.log")

# Create custom formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(lineno)d - %(message)s'
)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'
)

# Set up file handler with rotation: 5 MB max, keeping 3 backups
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5*1024*1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)  # Log all levels to file
file_handler.setFormatter(file_formatter)

# Set up console handler with configurable verbosity
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, CONSOLE_LOG_LEVEL, logging.INFO))  # Apply level from config
console_handler.setFormatter(console_formatter)

# Create a logger instance for the application
logger = logging.getLogger("DotaDiscordBot")
logger.setLevel(logging.DEBUG)  # Set logger to the lowest level, handlers control output

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Example usage: Log a debug message with context
logger.debug("Logger initialized with advanced configuration.")
