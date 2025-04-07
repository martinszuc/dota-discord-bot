"""
Authentication module for the Dota Discord Bot Dashboard (single admin from environment).
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, g
from dotenv import load_dotenv

auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger('DotaDiscordBot.WebApp')

# Read .env
load_dotenv()

# Grab admin credentials from environment
ENV_ADMIN_USER = os.getenv('ADMIN_USERNAME')
ENV_ADMIN_PASS = os.getenv('ADMIN_PASSWORD')

# We'll store active tokens in memory
active_tokens = {}

def require_auth(func):
    """Decorator to require a valid token."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'Missing or invalid token'}), 401

        token = auth_header.split(' ')[1]
        token_data = active_tokens.get(token)
        if not token_data:
            return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401

        # Put user info in flask.g
        g.user = token_data['username']
        g.role = token_data['role']
        return func(*args, **kwargs)
    return wrapper


@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Log in a user by checking the .env credentials only.
    Returns a JWT-like token in JSON if successful, else 401.
    """
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': 'Username and password are required'
        }), 400

    # Compare with environment-based admin
    if username == ENV_ADMIN_USER and password == ENV_ADMIN_PASS:
        # If correct, generate a token
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=12)

        active_tokens[token] = {
            'username': username,
            'role': 'admin',  # Hard-coded as admin
            'expiry': expiry.isoformat()
        }

        return jsonify({
            'status': 'success',
            'data': {
                'token': token,
                'username': username,
                'role': 'admin',
                'expiry': expiry.isoformat()
            }
        })
    else:
        # Invalid credentials
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401


@auth_blueprint.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Log out by removing the token from active_tokens."""
    token = request.headers['Authorization'].split(' ')[1]
    active_tokens.pop(token, None)
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})


# Clean out expired tokens before every request
@auth_blueprint.before_app_request
def cleanup_tokens():
    now = datetime.utcnow()
    expired = []
    for token, data in active_tokens.items():
        expiry = datetime.fromisoformat(data['expiry'])
        if expiry < now:
            expired.append(token)

    for token in expired:
        active_tokens.pop(token, None)
