# Discord Bot Hotkey Setup Tutorial

## Prerequisites

- **Discord Webhook URL**: Required for sending messages. Obtain it from your Discord server settings.
- **Python 3**: Ensure Python 3 is installed on your system.
- **xbindkeys and xdotool**: For hotkey setup on Linux/macOS.
- **AutoHotkey**: For hotkey setup on Windows.

---

## Step 1: Create Scripts for Commands

### Directory Structure

Run these commands to set up the directory:

```
mkdir -p ~/dota2_bot/scripts
cd ~/dota2_bot/scripts
```

### Scripts

Create the following scripts in `~/dota2_bot/scripts`. Replace `<YOUR_DISCORD_WEBHOOK_URL>` with your actual Discord webhook URL.

#### `send_discord_message.py`

```python
#!/usr/bin/env python3

import sys
import requests

def send_message(message):
    webhook_url = "<YOUR_DISCORD_WEBHOOK_URL>"
    data = {'content': message, 'username': 'Dota2Bot'}
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print(f"Message sent: {message}")
    else:
        print(f"Error: {response.status_code}, {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_discord_message.py <message>")
        sys.exit(1)
    send_message(' '.join(sys.argv[1:]))
```

### Other Command Scripts
#### command_rosh.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!rosh'
```
#### command_glyph.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!glyph'
```
#### command_tormentor.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!tormentor'
```
#### command_start.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!start 30'
```
#### command_pause.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!pause'
```
#### command_unpause.sh
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!unpause'
```

Make all scripts executable:

```
chmod +x ~/dota2_bot/scripts/*.sh
```

---

## Step 2: Linux Setup

1. Install required packages:
   ```
   sudo dnf install xbindkeys xdotool -y  # Fedora
   sudo apt-get install xbindkeys xdotool -y  # Debian/Ubuntu
   ```

2. Configure hotkeys:
   Open `~/.xbindkeysrc`:
   ```
   nano ~/.xbindkeysrc
   ```

   Add the following:
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

3. Start xbindkeys:
   ```
   xbindkeys
   ```
3. Stop xbindkeys if you want to disable hotkeys:
   ```
   killall xbindkeys
   ```
   
Test hotkeys by pressing the assigned keys. Check Discord for sent messages.

---

## Step 3: macOS Setup

1. Install xbindkeys and Python 3:
   ```
   brew install xbindkeys
   brew install python
   ```

2. Follow the [Linux Setup](#step-2-linux-setup) instructions. Use macOS paths where required.

---

## Step 4: Windows Setup

1. Install [AutoHotkey](https://www.autohotkey.com/).

2. Create a script with this content:
   ```ahk
   Numpad1::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!rosh"
   Numpad2::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!glyph"
   Numpad3::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!tormentor"
   Numpad4::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!start 30"
   Numpad5::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!pause"
   Numpad6::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!unpause"
   ```

3. Save and run the script. Test hotkeys to ensure functionality.

---

## Final Notes

- Replace `<YOUR_DISCORD_WEBHOOK_URL>` with your webhook URL in `send_discord_message.py`.
- Test your hotkeys for all platforms.
