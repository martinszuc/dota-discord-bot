# Discord Bot Hotkey Setup Tutorial

## Prerequisites

- **Discord Webhook URL**: Required for sending messages. Obtain it from your Discord server settings.
- **Python 3**: Ensure Python 3 is installed on your system.
- **xbindkeys and xdotool**: For hotkey setup on Linux/macOS.
- **AutoHotkey**: For hotkey setup on Windows.

My hotkeys setup:
    +---+
    | / |     /: Start Turbo (30 Sec Countdown)
+---+---+---+
| 7 | 8 | 9 | 7: Cancel RS Dead (RS Alive Again), 8: Cancel Enemy Glyph, 9: Stop Game
+---+---+---+
| 4 | 5 | 6 | 4: Start 01:20, 5: Pause, 6: Unpause
+---+---+---+
| 1 | 2 | 3 | 1: RS Killed, 2: Enemy Glyph, 3: Tormentor Killed
+---+---+---+

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
#### `command_rs.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!rs'
```

#### `command_glyph.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!g'
```

#### `command_tormentor.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!t'
```

#### `command_start.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!start 01:20'
```

#### `command_pause.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!pause'
```

#### `command_unpause.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!unpause'
```

#### `command_cancel_rs_alive.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!rsb'
```

#### `command_cancel_enemy_glyph.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!cg'
```

#### `command_stop_game.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!stop'
```

#### `command_start_turbo.sh`
```bash
#!/bin/bash
python3 ~/dota2_bot/scripts/send_discord_message.py '!start 30 turbo'
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
   "/home/your_username/dota2_bot/scripts/command_rs.sh"
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

   "/home/your_username/dota2_bot/scripts/command_cancel_rs_alive.sh"
       KP_Home

   "/home/your_username/dota2_bot/scripts/command_cancel_enemy_glyph.sh"
       KP_Up

   "/home/your_username/dota2_bot/scripts/command_stop_game.sh"
       KP_Prior

   "/home/your_username/dota2_bot/scripts/command_start_turbo.sh"
       KP_Divide
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
    Numpad1::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!rs"
    Numpad2::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!g
    Numpad3::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!t"
    Numpad4::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!start 01:20"
    Numpad5::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!pause"
    Numpad6::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!unpause"
    Numpad7::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!rsb"
    Numpad8::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!cg"
    Numpad9::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!stop"
    NumpadDiv::Run, pythonw.exe "C:\dota2_bot\scripts\send_discord_message.py" "!start 30 turbo"

   ```

3. Save and run the script. Test hotkeys to ensure functionality.

---

## Final Notes

- Replace `<YOUR_DISCORD_WEBHOOK_URL>` with your webhook URL in `send_discord_message.py`.
- Test your hotkeys for all platforms.
