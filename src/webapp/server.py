#!/usr/bin/env python3
"""
Main web server for the Dota Discord Bot Dashboard.
Serves the React frontend and provides API endpoints.
"""

import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# If you have other blueprints like api_blueprint, import them as needed:
# from backend.api import api_blueprint

# Import the new environment-based auth blueprint
from backend.auth import auth_blueprint

# Load environment variables from .env
load_dotenv()

app = Flask(__name__, static_folder='frontend/build')
CORS(app)

# Register your routes
# app.register_blueprint(api_blueprint, url_prefix='/api')  # If you still use it
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Serve the React build
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve the React frontend build files."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # For local dev, debug=True. Set to False in production
    app.run(host='0.0.0.0', port=port, debug=True)
