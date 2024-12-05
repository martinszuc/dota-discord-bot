# Use Python image with the correct version
FROM python:3.12-slim

# Set environment variables
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV WEBHOOK_ID=${WEBHOOK_ID}
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY pip_requirements.txt requirements.txt

# Install a compatible version of setuptools
RUN pip install --no-cache-dir 'setuptools<58.0.0'

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install FFmpeg (if not already installed)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the entire bot code into the container
COPY . /app

# Expose any ports if necessary (Discord bots don't need it, but for debug purposes)
EXPOSE 8080

# Command to run the bot
CMD ["python", "src/bot.py"]
