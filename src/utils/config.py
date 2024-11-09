# src/utils/config.py

import os
import yaml
import logging

# Set base directory to the current directory where the script is running
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
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

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

# Set up logging
LOG_FILE_PATH = os.path.join(LOG_DIR, "bot.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# Create a logger instance for the application
logger = logging.getLogger("DotaDiscordBot")
