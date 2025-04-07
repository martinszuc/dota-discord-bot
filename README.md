# Dota Timer Bot

<div align="center">
  <img src="https://github.com/user-attachments/assets/856f92b8-e669-4e8e-a5ba-810e704d5972" alt="Dota Timer Bot Logo" width="200"/>
  <h3>The Ultimate Dota 2 Timer and Notification System</h3>
  <p>Precision timing for Roshan, Glyphs, Tormentors, and critical game events.</p>
  
  ![Discord](https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
  ![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
</div>

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation Options](#installation-options)
  - [Method 1: Add the Bot to Your Server](#method-1-add-the-bot-to-your-server)
  - [Method 2: Self-Hosting with Docker](#method-2-self-hosting-with-docker)
  - [Method 3: Manual Installation](#method-3-manual-installation)
- [Setup Hotkeys](#setup-hotkeys)
- [Commands Guide](#commands-guide)
- [Web Dashboard](#web-dashboard)
- [Game State Integration (GSI)](#game-state-integration-gsi)
- [Advanced Configuration](#advanced-configuration)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🎮 Overview

The **Dota Timer Bot** transforms your Discord server into a powerful Dota 2 companion, providing precise timers, voice announcements, and helpful notifications for critical game events. With Game State Integration (GSI), the bot can automatically sync with your Dota 2 matches for a seamless experience.

Perfect for casual players and competitive teams alike, this bot helps you never miss Roshan spawns, rune timings, or important objectives again.

## ✨ Features

### Core Features

- **Game Timer** with support for both Regular and Turbo modes
- **Voice Announcements** for all timers and events
- **Text Notifications** in dedicated Discord channels
- **One-Click Hotkeys** for quick timer activation
- **Web Dashboard** for monitoring and control
- **Dota 2 GSI Integration** for automatic game synchronization

### Timer Types

- 🛡️ **Roshan Timer**: Tracks Roshan death and respawn window
- 🔮 **Glyph Timer**: Monitors enemy glyph cooldown
- 🐉 **Tormentor Timer**: Tracks Tormentor respawn
- ⏱️ **Game Timer**: Tracks match time with pause/unpause support
- 💎 **Rune Notifications**: Warns about upcoming rune spawns
- 🏆 **Custom Events**: Create your own timed events

### Special Features

- 💬 **Mindful Messages**: Optional positive reminders during games
- 🔄 **Auto-Sync**: Automatically detect and sync with your Dota 2 matches
- 🎯 **Audio Cues**: Distinct sounds for different event types
- 📊 **Statistics Tracking**: Monitor your team's performance (coming soon)

## 📥 Installation Options

### Method 1: Add the Bot to Your Server

The easiest way to get started is to invite the hosted bot to your Discord server:

1. Click [here](https://discord.com/oauth2/authorize?client_id=1302304488232583239&permissions=35191388204112&integration_type=0&scope=bot) to invite the bot to your server.
2. Create a text channel named `timer-bot` and a voice channel named `DOTA`.
3. You're ready to go! Type `!bot-help` to see available commands.

### Method 2: Self-Hosting with Docker

For advanced users who want to host their own instance:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/martinszuc/dota-discord-bot.git
   cd dota-discord-bot
   ```

2. **Create .env file:**
   ```env
   DISCORD_BOT_TOKEN=<your_discord_bot_token>
   WEBHOOK_ID=<your_webhook_id>
   ADMIN_USERNAME=<admin_username>
   ADMIN_PASSWORD=<admin_password>
   GSI_AUTH_TOKEN=<your_gsi_auth_token>
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the web dashboard:**
   Open `http://localhost:5000` in your browser

### Method 3: Manual Installation

For more control or if you prefer not to use Docker:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/martinszuc/dota-discord-bot.git
   cd dota-discord-bot
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -r pip_requirements.txt
   ```

3. **Set environment variables:**
   Create a `.env` file as in Method 2.

4. **Run the bot:**
   ```bash
   python run_bot.py
   ```

5. **Run the web dashboard (optional):**
   ```bash
   python run_webapp.py
   ```

## 🔧 Setup Hotkeys

For optimal gameplay, configure your Dota 2 hotkeys as described in [HOTKEYS_SETUP.md](HOTKEYS_SETUP.md).

This allows you to trigger timers with a single key press while playing, without needing to type commands.

Recommended hotkey layout:
```
    +---+
    | / |     /: Start Turbo (30 Sec Countdown)
+---+---+---+
| 7 | 8 | 9 | 7: Cancel RS Dead (RS Alive Again), 8: Cancel Enemy Glyph, 9: Stop Game
+---+---+---+
| 4 | 5 | 6 | 4: Start 01:20, 5: Pause, 6: Unpause
+---+---+---+
| 1 | 2 | 3 | 1: RS Killed, 2: Enemy Glyph, 3: Tormentor Killed
+---+---+---+
```

## 🤖 Commands Guide

### Game Timer Commands

- `!start <countdown> [mode]`: Start the game timer
  - Examples: `!start 45` or `!start -10:00 turbo`
- `!stop`: Stop the game timer
- `!pause` (Alias: `p`): Pause the timer
- `!unpause` (Aliases: `unp`, `up`): Resume the timer
- `!killall`: Stop all timers (Admin only)

### Objective Timers

- **Roshan Timer**:
  - `!rosh` (Aliases: `rs`, `rsdead`): Log Roshan's death
  - `!cancel-rosh` (Aliases: `rsalive`, `rsback`, `rsb`): Cancel Roshan timer

- **Glyph Timer**:
  - `!glyph` (Alias: `g`): Start enemy glyph cooldown
  - `!cancel-glyph` (Alias: `cg`): Cancel glyph timer

- **Tormentor Timer**:
  - `!tormentor` (Aliases: `tm`, `torm`, `t`): Log Tormentor's death
  - `!cancel-torm` (Aliases: `ct`): Cancel Tormentor timer

### Other Commands

- **Mindful Messages**:
  - `!enable-mindful` (Alias: `pma`): Enable mindful messages
  - `!disable-mindful` (Alias: `no-pma`): Disable mindful messages

- **Custom Events**:
  - `!add-event <type> <parameters>`: Add custom event
    - Example: `!add-event static 10:00 "Siege Creep incoming!"`
  - `!remove-event <event_id>`: Remove custom event
  - `!list-events` (Aliases: `ls`, `events`): List all events
  - `!reset-events`: Reset to default events

- **GSI Commands**:
  - `!gsi-status`: Check GSI connection status
  - `!gsi-sync`: Toggle automatic game sync

- **Help**:
  - `!bot-help` (Aliases: `help`, `pls`): Display help message

## 🖥️ Web Dashboard

The Dota Timer Bot includes a powerful web dashboard for monitoring and controlling your timers:

- **Dashboard**: View active timers, recent events, and system status
- **Game Controls**: Start, stop, pause, and manage timers
- **Events Manager**: Create and manage custom events
- **Settings**: Configure bot behavior
- **GSI Status**: Monitor your Dota 2 connection

### Accessing the Dashboard

If self-hosting, access the dashboard at:
- Local: `http://localhost:5000`
- Azure VM: `http://20.56.9.182:5000` (replace with your VM's IP)

Default credentials:
- Username: `admin` (or as set in .env)
- Password: `admin` (or as set in .env)

## 🔄 Game State Integration (GSI)

The bot supports Dota 2's Game State Integration (GSI) for automatic game synchronization:

### Setting Up GSI

1. Run the GSI configuration generator:
   ```bash
   python src/utils/gsi_config_creator.py
   ```

2. Follow the prompts to create a configuration file

3. Place the generated file in your Dota 2 GSI directory:
   ```
   [Steam Dir]/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/
   ```

4. Restart Dota 2

5. In Discord, use `!gsi-status` to check connection status
   
6. Use `!gsi-sync` to enable automatic timer synchronization

### Using GSI with Azure VM

If hosting on an Azure VM with public IP 20.56.9.182:

1. Run the Azure configuration script:
   ```bash
   python src/utils/azure_vm_config.py --ip 20.56.9.182
   ```

2. Follow the prompts to configure the VM and generate GSI files

3. Install the GSI config file as described above

## ⚙️ Advanced Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token | Required |
| `WEBHOOK_ID` | Discord webhook ID | Required |
| `ADMIN_USERNAME` | Web dashboard username | `admin` |
| `ADMIN_PASSWORD` | Web dashboard password | `admin` |
| `GSI_AUTH_TOKEN` | Dota 2 GSI auth token | Auto-generated |
| `HOST` | Web server host | `0.0.0.0` |
| `PORT` | Web server port | `5000` |
| `TZ` | Timezone | `UTC` |
| `LOG_LEVEL` | Console log level | `INFO` |
| `JSON_LOGGING` | Enable JSON logging | `false` |

### Config File

For more advanced configuration, edit `config.yaml`:

```yaml
prefix: "!"
timer_channel: "timer-bot"
voice_channel: "DOTA"
database_url: "sqlite:///bot.db"
console_log_level: "INFO"
```

## 🛠 Contributing

Thank you for your interest in contributing to this project! Please refer to the [CONTRIBUTORS](CONTRIBUTORS.md) file for detailed instructions.

To submit a change:

1. Fork the repository
2. Create a new branch 
3. Make your changes
4. Submit a pull request

For questions or assistance, contact: matoszuc@gmail.com

## 🔍 Troubleshooting

### Common Issues

- **Bot doesn't respond to commands**:
  - Ensure the bot has proper permissions
  - Verify the command channel is named `timer-bot`
  - Check bot logs for errors

- **Voice announcements not working**:
  - Ensure the voice channel is named `DOTA`
  - Check that ffmpeg is installed
  - Verify the bot has voice channel permissions

- **GSI not connecting**:
  - Confirm the GSI config file is in the correct location
  - Restart Dota 2 after installing the config
  - Check firewall settings
  - Make sure the auth token matches

### Getting Help

If you encounter issues not covered here:
1. Check the logs in the `logs/` directory
2. Join our [Discord support server](https://discord.gg/example) (coming soon)
3. Open an issue on GitHub
4. Contact the maintainer at matoszuc@gmail.com

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Enhance your Dota 2 experience with the Dota Timer Bot. GLHF! 🎮