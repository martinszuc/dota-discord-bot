import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if required environment variables are set
token = os.getenv('DISCORD_BOT_TOKEN')
webhook_id = os.getenv('WEBHOOK_ID')

if not token:
    print("Warning: DISCORD_BOT_TOKEN not found in .env file")
    print("Some bot functionality may not work correctly.")

if not webhook_id:
    print("Warning: WEBHOOK_ID not found in .env file")
    print("Webhook functionality may not work correctly.")

# Set PYTHONPATH to include the current directory
os.environ['PYTHONPATH'] = os.path.abspath('.')

# Run the webapp
print("Starting Dota Timer Bot web dashboard...")
os.system('python src/webapp/server.py')