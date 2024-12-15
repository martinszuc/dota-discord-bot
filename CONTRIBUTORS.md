# 🛠 Contributors Guide

- **Discord Webhook URL**: Required for sending messages. Obtain it from matoszuc@gmail.com for PMA ONLY server. Otherwise get ur own for local development for ur server.

## Running the Project in Docker
Follow these steps to set up and run the bot in a Docker environment:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/martinszuc/dota-discord-bot.git
   cd dota-discord-bot
   ```

2. **Set Up the Environment File:**
   Create a `.env` file in the project root directory with the following variables:
   ```env
   DISCORD_BOT_TOKEN=<your_discord_bot_token>
   WEBHOOK_ID=your_webhook_id
   ```

3. **Build the Docker Image:**
   Run the following command to build the Docker image:
   ```bash
   docker-compose build
   ```

4. **Run the Docker Container:**
   Start the bot using:
   ```bash
   docker-compose up
   ```

5. **Stop the Docker Container:**
   To stop the bot:
   ```bash
   docker-compose down
   ```

## Need Help?
If you encounter any issues or have questions, contact **matoszuc@gmail.com**
