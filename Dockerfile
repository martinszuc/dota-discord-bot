# Use Python 3.9.13 as the base image
FROM python:3.9.13-slim

# Set environment variables
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV WEBHOOK_ID=${WEBHOOK_ID}
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    ffmpeg && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy requirements file
COPY pip_requirements.txt requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the bot code
COPY . /app

# Expose any ports if necessary (Discord bots don't need it, but for debug purposes)
EXPOSE 8080

# Command to run the bot
CMD ["python", "src/bot.py"]
