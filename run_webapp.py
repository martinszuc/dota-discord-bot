#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required environment variables
REQUIRED_VARS = [
    ('ADMIN_USERNAME', 'Admin username for the web dashboard'),
    ('ADMIN_PASSWORD', 'Admin password for the web dashboard'),
    ('DISCORD_BOT_TOKEN', 'Discord bot token'),
    ('WEBHOOK_ID', 'Discord webhook ID')
]

missing_vars = []
for var_name, var_desc in REQUIRED_VARS:
    if not os.getenv(var_name):
        missing_vars.append(f"- {var_name}: {var_desc}")

if missing_vars:
    print("ERROR: The following required environment variables are missing:")
    for missing in missing_vars:
        print(missing)
    print("\nPlease add these to your .env file with appropriate values.")
    sys.exit(1)

# Set PYTHONPATH to include the current directory
os.environ['PYTHONPATH'] = os.path.abspath('.')

# Run the webapp
print("Starting Dota Timer Bot web dashboard...")
os.system('python src/webapp/server.py')