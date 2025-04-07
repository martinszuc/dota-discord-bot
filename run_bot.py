import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Check if token is set
token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    print("Error: DISCORD_BOT_TOKEN not found in .env file")
    exit(1)

# Run the bot with the correct PYTHONPATH
os.system('PYTHONPATH=. python src/bot.py')