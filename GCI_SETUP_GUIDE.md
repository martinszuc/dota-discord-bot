# Dota 2 GSI Setup and Verification Guide

This guide will help you set up and verify that Game State Integration (GSI) is working properly with the Dota Discord Bot.

## What is GSI?

Game State Integration allows external applications (like our Discord bot) to receive real-time game state information from Dota 2. This enables features like:

- Automatic timer synchronization
- Detection of key events (Roshan death, glyph usage, etc.)
- Accurate game time tracking

## Setup Steps

### 1. Create the GSI Configuration File

You need to place a configuration file in your Dota 2 GSI directory:

#### Automatic Setup (Recommended)

Run the GSI verification script:

```bash
python src/utils/gsi_verify.py
```

This will create a configuration file and start a temporary server to verify GSI data.

#### Manual Setup

Create a file named `gamestate_integration_dota_discord_bot.cfg` in your Dota 2 GSI configuration folder:

**Location:**
- Windows: `C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\cfg\gamestate_integration\`
- macOS: `~/Library/Application Support/Steam/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/`
- Linux: `~/.steam/steam/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/`

**File Content:**
```
"dota_discord_bot"
{
    "uri"           "http://localhost:5000/api/gsi"
    "timeout"       "5.0"
    "buffer"        "0.1"
    "throttle"      "0.1"
    "heartbeat"     "30.0"
    "data"
    {
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
    }
    "auth"
    {
        "token"         "your_secret_token"
    }
}
```

Replace `"your_secret_token"` with the value of your `GSI_AUTH_TOKEN` environment variable.

If you're using the bot on a remote server, replace `"http://localhost:5000/api/gsi"` with your server's address.

### 2. Restart Dota 2

After creating the configuration file, you need to restart Dota 2 completely.

### 3. Enable GSI Sync in the Bot

In Discord, use the command:
```
!gsi-sync
```

Or enable it through the web dashboard.

### 4. Verify GSI is Working

There are several ways to verify that GSI is working:

#### Method 1: Run the Verification Script

Run our verification script which creates a simple server to display GSI data:

```bash
python src/utils/gsi_verify.py
```

#### Method 2: Check Bot Dashboard

1. Open the web dashboard
2. Check the "GSI Status" section
3. It should show "Connected" when Dota 2 is running

#### Method 3: Check via Discord Command

Use the following command in Discord:
```
!gsi-status
```

## Troubleshooting

If GSI isn't working:

1. **Check Configuration File Location**
   Make sure the `.cfg` file is in the correct directory.

2. **Verify Dota 2 is Running**
   GSI only works when Dota 2 is running.

3. **Start or Spectate a Game**
   Most GSI data is only sent when you're in a game or spectating.

4. **Check File Permissions**
   Ensure the configuration file has the correct permissions.

5. **Firewall Issues**
   Check if your firewall is blocking the connection.

6. **Restart Dota 2**
   Sometimes a full restart of Dota 2 is required.

7. **Verify Token Match**
   Ensure the token in the config file matches your `GSI_AUTH_TOKEN` environment variable.

## Testing in Different Scenarios

### Practice Game

The easiest way to test GSI is to:
1. Start a practice game with bots
2. Use cheats to test specific scenarios:
   - `-startgame` to skip the draft
   - `-killroshan` to kill Roshan
   - `-respawnroshan` to respawn Roshan
   - `-refresh` to reset ability cooldowns

### Spectating

You can also test by spectating a live game - GSI data will still be sent.

## Need More Help?

If you're still having issues, contact us at matoszuc@gmail.com or create an issue on GitHub.