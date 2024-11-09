# src/config.py
import os
import yaml

# Define the path to the configuration file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")

# Load configuration data
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

# Load the config once and provide access to specific settings as constants
CONFIG = load_config()
PREFIX = CONFIG.get("prefix", "!")
TIMER_CHANNEL_NAME = CONFIG.get("timer_channel", "timer-bot")
VOICE_CHANNEL_NAME = CONFIG.get("voice_channel", "DOTA")
HTTP_SERVER_PORT = CONFIG.get("http_server_port", 8080)
DATABASE_URL = CONFIG.get("database_url", "sqlite:///bot.db")
