
# Discord Bot Hotkey Setup Tutorial

This guide provides instructions for setting up hotkeys on Linux, macOS, and Windows to automate commands for a Discord bot during Dota 2 gameplay. This will allow users to send specific commands to a Discord channel using designated hotkeys.

## Prerequisites

- **Discord Webhook URL**: You’ll need a Discord webhook URL, which can be requested and generated from your server settings.
- **Python 3**: Ensure Python 3 is installed on your system.
- **Discord Bot Files**: Obtain the necessary files and scripts for your bot's setup.

## Supported Platforms

1. [Linux Setup](#linux-setup)
2. [macOS Setup](#macos-setup)
3. [Windows Setup](#windows-setup)

---

## Linux Setup

### Step 1: Install Required Packages

Open your terminal and run:

```
sudo dnf install xbindkeys xdotool -y  # For Fedora
sudo apt-get install xbindkeys xdotool -y  # For Debian/Ubuntu
```

### Step 2: Create a Directory Structure

Create a directory for the bot files:

```
mkdir -p ~/dota2_bot/scripts
cd ~/dota2_bot/scripts
```

### Step 3: Add Your Webhook URL

In each script below, replace `<YOUR_DISCORD_WEBHOOK_URL>` with your Discord webhook URL.

### Step 4: Create Command Scripts

Create the following scripts in the `~/dota2_bot/scripts` directory:

1. **command_rosh.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!rosh'
```

2. **command_glyph.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!glyph'
```

3. **command_tormentor.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!tormentor'
```

4. **command_start.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!start 1800 regular mention'
```

5. **command_pause.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!pause'
```

6. **command_unpause.sh**

```
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!unpause'
```

Ensure each script is executable:

```
chmod +x ~/dota2_bot/scripts/*.sh
```

### Step 5: Configure xbindkeys

Open `~/.xbindkeysrc`:

```
nano ~/.xbindkeysrc
```

Add the following lines:

```
"/home/your_username/dota2_bot/scripts/command_rosh.sh"
    KP_End

"/home/your_username/dota2_bot/scripts/command_glyph.sh"
    KP_Down

"/home/your_username/dota2_bot/scripts/command_tormentor.sh"
    KP_Next

"/home/your_username/dota2_bot/scripts/command_start.sh"
    KP_Left

"/home/your_username/dota2_bot/scripts/command_pause.sh"
    KP_Begin

"/home/your_username/dota2_bot/scripts/command_unpause.sh"
    KP_Right
```

Save and exit.

### Step 6: Test xbindkeys Configuration

Start `xbindkeys`:

```
xbindkeys
```

Press the assigned keys to test each command. Check your Discord channel for corresponding messages.

---

## macOS Setup

### Step 1: Install xbindkeys and Python 3

```
brew install xbindkeys
brew install python
```

### Step 2: Follow the Linux Guide

macOS users can follow the [Linux setup instructions](#linux-setup), as they are similar. Use macOS paths where needed.

---

## Windows Setup

Windows does not have native xbindkeys support. Use the following alternative:

### Step 1: Install AutoHotkey

1. Download and install [AutoHotkey](https://www.autohotkey.com/).
2. Create a new AutoHotkey script with the following content:

```
Numpad1::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!rosh"
Numpad2::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!glyph"
Numpad3::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!tormentor"
Numpad4::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!start 1800 regular mention"
Numpad5::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!pause"
Numpad6::Run, pythonw.exe "C:\path\to\send_discord_message.py" "!unpause"
```

Replace `C:\path\to` with the actual path to your Python script. Save and double-click the script to activate the hotkeys.

---

## Discord Message Script (send_discord_message.py)

Use the following Python script in `~/dota2_bot/scripts` to send messages to Discord:

```
#!/usr/bin/env python3
import sys
import os
import requests

def send_message(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Webhook URL not set.")
        sys.exit(1)
    data = {"content": message}
    requests.post(webhook_url, json=data)

if __name__ == "__main__":
    send_message(sys.argv[1])
```

Make this file executable:

```
chmod +x ~/dota2_bot/scripts/send_discord_message.py
```

---

## Final Notes

Test each hotkey to ensure it works and sends the correct command to Discord. If issues arise, verify your setup and environment variables.