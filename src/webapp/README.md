# Dota Timer Bot Web Dashboard

A web-based UI for controlling and monitoring the Dota Timer Bot.

## Features

- **Centralized Dashboard**: Monitor game timers and bot status from a single interface
- **Game Controls**: Start, stop, pause, and unpause game timers
- **Special Timers**: Manage Roshan, Glyph, and Tormentor timers
- **Event Management**: Add, edit, and remove custom events
- **Settings Management**: Configure bot settings through a user-friendly interface
- **User Authentication**: Secure access with user accounts and permissions

## Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- npm or yarn

## Installation

### Backend Setup

1. Navigate to the webapp directory:
   ```bash
   cd src/webapp
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install backend dependencies:
   ```bash
   pip install flask flask-cors
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd src/webapp/frontend
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   # OR
   yarn install
   ```

## Running the Application

### Development Mode

1. Start the Flask backend (from the `src/webapp` directory):
   ```bash
   python server.py
   ```

2. In a separate terminal, start the React frontend (from the `src/webapp/frontend` directory):
   ```bash
   npm start
   # OR
   yarn start
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

### Production Mode

1. Build the frontend:
   ```bash
   cd src/webapp/frontend
   npm run build
   # OR
   yarn build
   ```

2. Start the Flask server (from the `src/webapp` directory):
   ```bash
   python server.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Default Credentials

The web dashboard comes with a default admin account:

- **Username**: admin
- **Password**: admin

It's recommended to change the password after the first login.

## Adding New Users

1. Log in as an admin.
2. Navigate to the Settings page.
3. In the User Management section, click "Add User".
4. Fill in the username, password, and role.
5. Click "Create User".

## Adding to Docker

To include the web dashboard in your Docker setup, modify the Dockerfile to install the required dependencies and build the frontend. See the Dockerfile for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.