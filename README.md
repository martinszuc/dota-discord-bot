# README

## Dota Timer Bot

The **Dota Timer Bot** is a Discord bot designed to provide precise timers and notifications for critical Dota 2 game events. With this bot, you can enhance your in-game strategies and stay ahead of your opponents.

### 📥 Add the Bot to Your Server:
Click [here](https://discord.com/oauth2/authorize?client_id=1302304488232583239&permissions=35191388204112&integration_type=0&scope=bot) to invite the bot to your Discord server. 

**For commands use text channel `timer-bot` and voice channel `DOTA` which you should create on your server**

- ![image](https://github.com/user-attachments/assets/856f92b8-e669-4e8e-a5ba-810e704d5972)

### 🔧 Setting Up Hotkeys:
For an optimal experience, configure your Dota 2 hotkeys as described in [HOTKEYS_SETUP.md](HOTKEYS_SETUP.md).

### 🤖 Commands

#### 📅 **Game Timer**:
- `!start <countdown> [mode]`: Start the game timer. *(Example: `!start 45` or `!start -10:00 turbo`)*
- `!stop`: Stop the game timer.
- `!pause` *(Alias: `p`)*: Pause the game timer.
- `!unpause` *(Aliases: `unp`, `up`)*: Resume the game timer.
- `!killall`: Stop all timers (Admin only).

#### 🛡️ **Roshan Timer**:
- `!rosh` *(Aliases: `rs`, `rsdead`, `rs-dead`, `rsdied`, `rs-died`)*: Log Roshan's death and start respawn timer.
- `!cancel-rosh` *(Aliases: `rsalive`, `rsback`, `rsb`)*: Cancel Roshan respawn timer.

#### 🔮 **Glyph Timer**:
- `!glyph` *(Alias: `g`)*: Start a 5-minute glyph cooldown timer.
- `!cancel-glyph` *(Alias: `cg`)*: Cancel the glyph cooldown timer.

#### 🐉 **Tormentor Timer**:
- `!tormentor` *(Aliases: `tm`, `torm`, `t`)*: Log Tormentor's death and start respawn timer.
- `!cancel-torm` *(Aliases: `ct`, `tormentorcancel`)*: Cancel Tormentor respawn timer.

#### 💬 **Mindful Messages**:
- `!enable-mindful` *(Aliases: `enable-pma`, `pma`)*: Enable periodic mindful messages.
- `!disable-mindful` *(Aliases: `disable-pma`, `no-pma`)*: Disable mindful messages.

#### ⚙️ **Custom Events**:
- `!add-event <type> <parameters>`: Add a custom event. *(Example: `!add-event static 10:00 "Siege Creep incoming!"`)*
- `!remove-event <event_id>`: Remove a custom event by ID.
- `!list-events` *(Aliases: `ls`, `events`)*: List all custom events.
- `!reset-events`: Reset all events to default.

#### ℹ️ **General**:
- `!bot-help` *(Aliases: `dota-help`, `dotahelp`, `pls`, `help`)*: Display help message with commands.

---

### 🛠 Contributing
Feel free to fork this repository and submit pull requests. Contributions are always welcome!

### 📜 License
This project is licensed under the MIT License.

---

Enhance your Dota 2 experience with the Dota Timer Bot. GLHF! 🎮
