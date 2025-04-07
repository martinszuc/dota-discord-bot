#!/usr/bin/env python3
"""
GSI Verification Script

This script helps verify that GSI (Game State Integration) is properly set up and working.
It creates a config file for GSI and monitors incoming GSI data.
"""

import os
import time
import argparse
import json
import http.server
import socketserver
import sys

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.config import logger

# Default auth token
DEFAULT_AUTH_TOKEN = "your_secret_token"


class GSIHandler(http.server.BaseHTTPRequestHandler):
    """Handler for GSI HTTP requests."""

    def do_POST(self):
        """Handle POST requests with GSI data."""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
            auth_token = data.get('auth', {}).get('token')

            # Check authentication
            if auth_token != self.server.auth_token:
                print(f"❌ Invalid auth token: {auth_token}")
                self.send_response(401)
                self.end_headers()
                return

            # Process GSI data
            self._process_gsi_data(data)

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))

        except Exception as e:
            print(f"❌ Error processing request: {e}")
            self.send_response(500)
            self.end_headers()

    def _process_gsi_data(self, data):
        """Process and display GSI data."""
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        print(f"\n⏰ [{timestamp}] Received GSI update:")

        # Extract important information
        if 'map' in data:
            map_data = data['map']
            game_state = map_data.get('game_state', 'unknown')
            game_time = map_data.get('game_time')
            match_id = map_data.get('matchid')

            # Game state
            state_icon = '✅' if game_state == 'DOTA_GAMERULES_STATE_GAME_IN_PROGRESS' else '⏳'
            print(f"{state_icon} Game State: {game_state}")

            # Game time
            if game_time is not None:
                minutes = int(game_time) // 60
                seconds = int(game_time) % 60
                print(f"⏱️ Game Time: {minutes:02d}:{seconds:02d}")

            # Match ID
            if match_id:
                print(f"🆔 Match ID: {match_id}")

        # Player info
        if 'player' in data:
            player = data['player']
            name = player.get('name')
            team = player.get('team_name') or ('Radiant' if player.get('team_number') == 0 else 'Dire')

            if name:
                print(f"👤 Player: {name} ({team})")

        # Hero info
        if 'hero' in data:
            hero = data['hero']
            hero_name = hero.get('name', '').replace('npc_dota_hero_', '')
            level = hero.get('level')

            if hero_name:
                print(f"🦸 Hero: {hero_name} (Level {level})")

        # Buildings info
        if 'buildings' in data:
            buildings = data['buildings']
            radiant_glyph = buildings.get('radiant', {}).get('glyph', {}).get('cooldown', -1)
            dire_glyph = buildings.get('dire', {}).get('glyph', {}).get('cooldown', -1)

            print(f"🔮 Glyphs - Radiant: {'Cooldown' if radiant_glyph > 0 else 'Available'}, "
                  f"Dire: {'Cooldown' if dire_glyph > 0 else 'Available'}")

        # Events
        if 'events' in data and data['events']:
            print("📣 Recent Events:")
            for event in data['events'][-3:]:  # Show last 3 events
                print(f"  • {event.get('type')}")


def create_gsi_config(port, auth_token):
    """Create a GSI configuration file."""
    config_dir = os.path.expanduser("~/gamestate_integration")
    os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, "gamestate_integration_gsi_verify.cfg")

    config_content = f"""
"GSI Verification"
{{
    "uri"           "http://localhost:{port}"
    "timeout"       "5.0"
    "buffer"        "0.1"
    "throttle"      "0.1"
    "heartbeat"     "30.0"
    "data"
    {{
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "draft"         "1"
        "wearables"     "0"
        "buildings"     "1"
        "events"        "1"
        "gamestate"     "1"
    }}
    "auth"
    {{
        "token"         "{auth_token}"
    }}
}}
"""

    with open(config_path, 'w') as f:
        f.write(config_content)

    print(f"\n✅ Created GSI config file at: {config_path}")
    print(f"⚠️ IMPORTANT: You need to copy this file to your Dota 2 GSI directory:")
    print("   [Steam Dir]/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/")
    print("\n   On Windows, typically:")
    print("   C:\\Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta\\game\\dota\\cfg\\gamestate_integration\\")
    print("\n   On macOS, typically:")
    print("   ~/Library/Application Support/Steam/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/")
    print("\n   On Linux, typically:")
    print("   ~/.steam/steam/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/")

    return config_path


def main():
    parser = argparse.ArgumentParser(description="GSI Verification Tool")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on (default: 3000)")
    parser.add_argument("--auth", type=str, default=DEFAULT_AUTH_TOKEN, help="Auth token for GSI")
    args = parser.parse_args()

    # Create GSI config file
    config_path = create_gsi_config(args.port, args.auth)

    print(f"\n🚀 Starting GSI verification server on port {args.port}...")
    print("⌛ Waiting for GSI data from Dota 2...")
    print("ℹ️ Make sure to copy the config file and restart Dota 2 if you haven't already.")
    print("ℹ️ You need to be in a game (or spectating) to receive GSI data.")
    print("\n📋 Instructions to verify:")
    print("   1. Copy the config file to your Dota 2 GSI directory")
    print("   2. Restart Dota 2")
    print("   3. Start a game or spectate a match")
    print("   4. Watch for GSI data below")
    print("\n⚠️ Press Ctrl+C to stop the server")

    # Create and start the server
    class GSIServer(socketserver.TCPServer):
        def __init__(self, server_address, handler_class, auth_token):
            super().__init__(server_address, handler_class)
            self.auth_token = auth_token

    server = GSIServer(("", args.port), GSIHandler, args.auth)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 GSI verification server stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()