# Use Python image with the correct version
FROM python:3.10-slim

# Set environment variables
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV WEBHOOK_ID=${WEBHOOK_ID}

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY pip_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire bot code into the container
COPY . /app

# Expose any ports if necessary (Discord bots don't need it, but for debug purposes)
EXPOSE 8080

# Command to run the bot
CMD ["python", "src/bot.py"]
