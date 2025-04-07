# Use Python 3.9.13 as the base image
FROM python:3.9.13-slim

# Set environment variables
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV WEBHOOK_ID=${WEBHOOK_ID}
ENV PYTHONPATH=/app
ENV NODE_VERSION=16.x

# Set the working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    ffmpeg \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for the web dashboard
RUN curl -sL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy requirements file
COPY pip_requirements.txt requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt \
    && pip install flask flask-cors gunicorn

# Copy the bot code
COPY . /app

# Build the React frontend
WORKDIR /app/src/webapp/frontend
RUN npm install && npm run build

# Return to the app directory
WORKDIR /app

# Expose port for the web dashboard
EXPOSE 5000

# Command to run both the bot and the web dashboard
CMD ["sh", "-c", "python src/bot.py & python src/webapp/server.py"]